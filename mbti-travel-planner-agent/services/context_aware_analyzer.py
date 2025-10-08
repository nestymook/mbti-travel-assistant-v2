"""
Context-Aware Intent Analysis

This module provides advanced context-aware analysis for the MBTI Travel Planner Agent,
enabling personalized intent detection based on user history, MBTI personality types,
and conversation patterns.

Features:
- User context integration for personalized intent detection
- Conversation history analysis for improved accuracy
- MBTI-aware parameter extraction and preference handling
- Temporal pattern recognition
- Preference learning and adaptation
"""

import logging
from typing import Dict, Any, Optional, List, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import json
import re

from .intent_analyzer import IntentAnalyzer, ParameterType
from .orchestration_types import RequestType, Intent, UserContext


@dataclass
class ConversationPattern:
    """Pattern detected in conversation history."""
    pattern_type: str
    frequency: int
    confidence: float
    last_occurrence: datetime
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MBTIPreferences:
    """MBTI-based preferences for restaurant recommendations."""
    mbti_type: str
    cuisine_preferences: List[str] = field(default_factory=list)
    atmosphere_preferences: List[str] = field(default_factory=list)
    group_size_preferences: List[str] = field(default_factory=list)
    meal_timing_preferences: List[str] = field(default_factory=list)
    exploration_tendency: float = 0.5  # 0.0 = conservative, 1.0 = adventurous
    social_preference: float = 0.5     # 0.0 = intimate, 1.0 = social
    
    @classmethod
    def from_mbti_type(cls, mbti_type: str) -> 'MBTIPreferences':
        """Create preferences based on MBTI type."""
        preferences = cls(mbti_type=mbti_type)
        
        # Extraversion vs Introversion
        if mbti_type[0] == 'E':
            preferences.social_preference = 0.7
            preferences.atmosphere_preferences.extend(['lively', 'social', 'bustling'])
            preferences.group_size_preferences.extend(['group', 'large group'])
        else:
            preferences.social_preference = 0.3
            preferences.atmosphere_preferences.extend(['quiet', 'intimate', 'cozy'])
            preferences.group_size_preferences.extend(['solo', 'couple', 'small group'])
        
        # Sensing vs Intuition
        if mbti_type[1] == 'S':
            preferences.exploration_tendency = 0.3
            preferences.cuisine_preferences.extend(['traditional', 'familiar', 'comfort food'])
        else:
            preferences.exploration_tendency = 0.7
            preferences.cuisine_preferences.extend(['fusion', 'innovative', 'exotic'])
        
        # Thinking vs Feeling
        if mbti_type[2] == 'T':
            preferences.atmosphere_preferences.extend(['efficient', 'professional'])
        else:
            preferences.atmosphere_preferences.extend(['warm', 'friendly', 'welcoming'])
        
        # Judging vs Perceiving
        if mbti_type[3] == 'J':
            preferences.meal_timing_preferences.extend(['scheduled', 'planned', 'regular hours'])
        else:
            preferences.meal_timing_preferences.extend(['flexible', 'spontaneous', 'late night'])
        
        return preferences


@dataclass
class UserProfile:
    """Comprehensive user profile for context-aware analysis."""
    user_id: str
    mbti_preferences: Optional[MBTIPreferences] = None
    conversation_patterns: List[ConversationPattern] = field(default_factory=list)
    learned_preferences: Dict[str, Any] = field(default_factory=dict)
    request_history: List[Dict[str, Any]] = field(default_factory=list)
    success_patterns: Dict[str, float] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.now)
    
    def add_request(self, request: str, intent: Intent, success: bool = True):
        """Add a request to the user's history."""
        self.request_history.append({
            'timestamp': datetime.now(),
            'request': request,
            'intent_type': intent.type.value,
            'parameters': intent.parameters,
            'confidence': intent.confidence,
            'success': success
        })
        
        # Keep only recent history
        cutoff_date = datetime.now() - timedelta(days=30)
        self.request_history = [
            req for req in self.request_history 
            if req['timestamp'] > cutoff_date
        ]
        
        self.last_updated = datetime.now()
    
    def get_frequent_patterns(self, min_frequency: int = 2) -> List[ConversationPattern]:
        """Get frequently occurring patterns."""
        return [pattern for pattern in self.conversation_patterns 
                if pattern.frequency >= min_frequency]


class ContextAwareAnalyzer:
    """
    Advanced context-aware analyzer for personalized intent detection.
    
    This analyzer provides:
    - User profile management and learning
    - MBTI-based preference analysis
    - Conversation pattern recognition
    - Temporal analysis of user behavior
    - Adaptive confidence scoring
    """
    
    def __init__(self, base_analyzer: IntentAnalyzer):
        """
        Initialize the context-aware analyzer.
        
        Args:
            base_analyzer: Base intent analyzer to enhance
        """
        self.base_analyzer = base_analyzer
        self.logger = logging.getLogger(f"mbti_travel_planner.context_analyzer")
        
        # User profiles cache
        self._user_profiles: Dict[str, UserProfile] = {}
        
        # Pattern recognition settings
        self._pattern_confidence_threshold = 0.6
        self._temporal_weight = 0.2
        self._mbti_weight = 0.3
        self._history_weight = 0.25
        
        # MBTI type mappings
        self._mbti_cuisine_mapping = self._initialize_mbti_cuisine_mapping()
        self._mbti_atmosphere_mapping = self._initialize_mbti_atmosphere_mapping()
        
        self.logger.info("Context-aware analyzer initialized")
    
    async def analyze_intent_with_context(self, 
                                        request: str,
                                        context: UserContext) -> Intent:
        """
        Analyze intent with full context awareness.
        
        Args:
            request: User's request text
            context: User context information
            
        Returns:
            Enhanced intent with context-aware analysis
        """
        # Get base intent analysis
        base_intent = await self.base_analyzer.analyze_intent(request, context)
        
        if not context or not context.user_id:
            return base_intent
        
        # Get or create user profile
        user_profile = self._get_or_create_user_profile(context)
        
        # Apply context-aware enhancements
        enhanced_intent = await self._enhance_intent_with_context(
            base_intent, request, context, user_profile
        )
        
        # Update user profile with new request
        user_profile.add_request(request, enhanced_intent)
        
        return enhanced_intent
    
    def analyze_conversation_history(self, 
                                   context: UserContext) -> List[ConversationPattern]:
        """
        Analyze conversation history to identify patterns.
        
        Args:
            context: User context with conversation history
            
        Returns:
            List of detected conversation patterns
        """
        if not context.conversation_history:
            return []
        
        patterns = []
        
        # Analyze request type patterns
        request_types = []
        for hist_request in context.conversation_history:
            intent_type = self.base_analyzer.classify_request_type(hist_request)
            request_types.append(intent_type)
        
        # Find frequent request types
        type_counts = Counter(request_types)
        for req_type, count in type_counts.items():
            if count >= 2:  # Minimum frequency
                patterns.append(ConversationPattern(
                    pattern_type=f"frequent_{req_type.value}",
                    frequency=count,
                    confidence=min(1.0, count / len(request_types)),
                    last_occurrence=datetime.now()
                ))
        
        # Analyze parameter patterns
        parameter_patterns = self._analyze_parameter_patterns(context.conversation_history)
        patterns.extend(parameter_patterns)
        
        # Analyze temporal patterns
        temporal_patterns = self._analyze_temporal_patterns(context.conversation_history)
        patterns.extend(temporal_patterns)
        
        return patterns
    
    def extract_mbti_preferences(self, 
                               request: str,
                               mbti_type: str) -> Dict[str, Any]:
        """
        Extract MBTI-aware preferences from request.
        
        Args:
            request: User's request text
            mbti_type: User's MBTI personality type
            
        Returns:
            Dictionary of MBTI-aware preferences
        """
        preferences = {}
        
        # Get MBTI preferences
        mbti_prefs = MBTIPreferences.from_mbti_type(mbti_type)
        
        # Apply MBTI-based cuisine preferences
        request_lower = request.lower()
        
        # Check for cuisine alignment with MBTI
        for cuisine in mbti_prefs.cuisine_preferences:
            if cuisine.lower() in request_lower:
                preferences['mbti_cuisine_match'] = cuisine
                preferences['mbti_confidence_boost'] = 0.2
                break
        
        # Check for atmosphere preferences
        for atmosphere in mbti_prefs.atmosphere_preferences:
            if atmosphere.lower() in request_lower:
                preferences['mbti_atmosphere_match'] = atmosphere
                preferences['mbti_confidence_boost'] = preferences.get('mbti_confidence_boost', 0) + 0.1
                break
        
        # Add exploration tendency
        preferences['exploration_tendency'] = mbti_prefs.exploration_tendency
        preferences['social_preference'] = mbti_prefs.social_preference
        
        # Suggest MBTI-aligned parameters
        if 'group_size' not in preferences:
            preferences['suggested_group_size'] = mbti_prefs.group_size_preferences[0]
        
        return preferences
    
    def _get_or_create_user_profile(self, context: UserContext) -> UserProfile:
        """Get existing user profile or create new one."""
        user_id = context.user_id
        
        if user_id not in self._user_profiles:
            profile = UserProfile(user_id=user_id)
            
            # Initialize MBTI preferences if available
            if context.mbti_type:
                profile.mbti_preferences = MBTIPreferences.from_mbti_type(context.mbti_type)
            
            self._user_profiles[user_id] = profile
        
        return self._user_profiles[user_id]
    
    async def _enhance_intent_with_context(self, 
                                         base_intent: Intent,
                                         request: str,
                                         context: UserContext,
                                         user_profile: UserProfile) -> Intent:
        """Enhance base intent with context-aware analysis."""
        enhanced_parameters = base_intent.parameters.copy()
        enhanced_confidence = base_intent.confidence
        
        # Apply MBTI-based enhancements
        if context.mbti_type:
            mbti_preferences = self.extract_mbti_preferences(request, context.mbti_type)
            enhanced_parameters.update(mbti_preferences)
            
            # Boost confidence for MBTI-aligned requests
            if 'mbti_confidence_boost' in mbti_preferences:
                enhanced_confidence += mbti_preferences['mbti_confidence_boost']
        
        # Apply conversation history analysis
        if context.conversation_history:
            history_boost = self._calculate_history_confidence_boost(
                base_intent, context.conversation_history, user_profile
            )
            enhanced_confidence += history_boost
        
        # Apply learned preferences
        if user_profile.learned_preferences:
            preference_boost = self._calculate_preference_alignment_boost(
                request, user_profile.learned_preferences
            )
            enhanced_confidence += preference_boost
        
        # Apply temporal patterns
        temporal_boost = self._calculate_temporal_confidence_boost(
            base_intent, user_profile
        )
        enhanced_confidence += temporal_boost
        
        # Ensure confidence stays within bounds
        enhanced_confidence = min(1.0, max(0.0, enhanced_confidence))
        
        # Add context-aware capabilities
        enhanced_optional_capabilities = base_intent.optional_capabilities.copy()
        
        if context.mbti_type:
            enhanced_optional_capabilities.append('mbti_personalization')
        
        if user_profile.learned_preferences:
            enhanced_optional_capabilities.append('preference_personalization')
        
        # Create enhanced intent
        enhanced_intent = Intent(
            type=base_intent.type,
            confidence=enhanced_confidence,
            parameters=enhanced_parameters,
            required_capabilities=base_intent.required_capabilities,
            optional_capabilities=enhanced_optional_capabilities
        )
        
        return enhanced_intent
    
    def _analyze_parameter_patterns(self, history: List[str]) -> List[ConversationPattern]:
        """Analyze patterns in extracted parameters."""
        patterns = []
        
        # Extract parameters from each historical request
        all_parameters = []
        for hist_request in history:
            params = self.base_analyzer._extract_parameters(hist_request, RequestType.UNKNOWN)
            all_parameters.append(params)
        
        # Find frequent districts
        districts = []
        for params in all_parameters:
            if 'districts' in params:
                districts.extend(params['districts'])
        
        if districts:
            district_counts = Counter(districts)
            for district, count in district_counts.items():
                if count >= 2:
                    patterns.append(ConversationPattern(
                        pattern_type="frequent_district",
                        frequency=count,
                        confidence=count / len(history),
                        last_occurrence=datetime.now(),
                        parameters={'district': district}
                    ))
        
        # Find frequent meal types
        meal_types = []
        for params in all_parameters:
            if 'meal_types' in params:
                meal_types.extend(params['meal_types'])
        
        if meal_types:
            meal_counts = Counter(meal_types)
            for meal, count in meal_counts.items():
                if count >= 2:
                    patterns.append(ConversationPattern(
                        pattern_type="frequent_meal_type",
                        frequency=count,
                        confidence=count / len(history),
                        last_occurrence=datetime.now(),
                        parameters={'meal_type': meal}
                    ))
        
        return patterns
    
    def _analyze_temporal_patterns(self, history: List[str]) -> List[ConversationPattern]:
        """Analyze temporal patterns in conversation history."""
        patterns = []
        
        # For now, implement simple temporal analysis
        # In a real system, this would analyze timestamps and detect time-based patterns
        
        if len(history) >= 3:
            # Detect if user frequently asks similar questions
            similarity_scores = []
            for i in range(len(history) - 1):
                similarity = self.base_analyzer._calculate_request_similarity(
                    history[i], history[i + 1]
                )
                similarity_scores.append(similarity)
            
            avg_similarity = sum(similarity_scores) / len(similarity_scores)
            
            if avg_similarity > 0.6:
                patterns.append(ConversationPattern(
                    pattern_type="repetitive_requests",
                    frequency=len(history),
                    confidence=avg_similarity,
                    last_occurrence=datetime.now(),
                    parameters={'avg_similarity': avg_similarity}
                ))
        
        return patterns
    
    def _calculate_history_confidence_boost(self, 
                                          intent: Intent,
                                          history: List[str],
                                          user_profile: UserProfile) -> float:
        """Calculate confidence boost based on conversation history."""
        boost = 0.0
        
        # Check for similar intent types in history
        similar_count = 0
        for hist_request in history[-5:]:  # Check last 5 requests
            hist_intent_type = self.base_analyzer.classify_request_type(hist_request)
            if hist_intent_type == intent.type:
                similar_count += 1
        
        if similar_count > 0:
            boost += (similar_count / 5) * self._history_weight
        
        # Check success patterns
        if intent.type.value in user_profile.success_patterns:
            success_rate = user_profile.success_patterns[intent.type.value]
            boost += success_rate * 0.1
        
        return boost
    
    def _calculate_preference_alignment_boost(self, 
                                            request: str,
                                            preferences: Dict[str, Any]) -> float:
        """Calculate confidence boost based on learned preferences."""
        boost = 0.0
        request_lower = request.lower()
        
        # Check cuisine preferences
        if 'preferred_cuisines' in preferences:
            for cuisine in preferences['preferred_cuisines']:
                if cuisine.lower() in request_lower:
                    boost += 0.1
        
        # Check district preferences
        if 'preferred_districts' in preferences:
            for district in preferences['preferred_districts']:
                if district.lower() in request_lower:
                    boost += 0.1
        
        # Check meal preferences
        if 'preferred_meal_times' in preferences:
            for meal in preferences['preferred_meal_times']:
                if meal.lower() in request_lower:
                    boost += 0.05
        
        return min(0.3, boost)  # Cap the boost
    
    def _calculate_temporal_confidence_boost(self, 
                                           intent: Intent,
                                           user_profile: UserProfile) -> float:
        """Calculate confidence boost based on temporal patterns."""
        boost = 0.0
        
        # Check if this is a typical time for this type of request
        current_hour = datetime.now().hour
        
        # Simple temporal logic
        if intent.type == RequestType.RESTAURANT_SEARCH_BY_MEAL:
            if 'meal_types' in intent.parameters:
                meal_types = intent.parameters['meal_types']
                
                if 'breakfast' in meal_types and 6 <= current_hour <= 11:
                    boost += 0.1
                elif 'lunch' in meal_types and 11 <= current_hour <= 15:
                    boost += 0.1
                elif 'dinner' in meal_types and 17 <= current_hour <= 22:
                    boost += 0.1
        
        return boost
    
    def _initialize_mbti_cuisine_mapping(self) -> Dict[str, List[str]]:
        """Initialize MBTI to cuisine preference mapping."""
        return {
            'E': ['social dining', 'buffet', 'group-friendly'],
            'I': ['intimate', 'quiet', 'cozy'],
            'S': ['traditional', 'comfort food', 'familiar'],
            'N': ['fusion', 'innovative', 'experimental'],
            'T': ['efficient service', 'value-focused'],
            'F': ['warm atmosphere', 'family-friendly'],
            'J': ['structured dining', 'reservations'],
            'P': ['casual', 'flexible', 'spontaneous']
        }
    
    def _initialize_mbti_atmosphere_mapping(self) -> Dict[str, List[str]]:
        """Initialize MBTI to atmosphere preference mapping."""
        return {
            'E': ['lively', 'bustling', 'social'],
            'I': ['quiet', 'peaceful', 'intimate'],
            'S': ['comfortable', 'familiar', 'traditional'],
            'N': ['unique', 'creative', 'inspiring'],
            'T': ['professional', 'efficient', 'clean'],
            'F': ['warm', 'welcoming', 'friendly'],
            'J': ['organized', 'structured', 'predictable'],
            'P': ['relaxed', 'flexible', 'casual']
        }