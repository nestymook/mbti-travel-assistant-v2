"""MBTI Personality Processing Service for MBTI Travel Assistant.

This module implements MBTI personality validation, trait mapping, and personality-specific
tourist spot matching logic. It provides fast query optimization based on test_single_mbti_type.py
patterns and integrates with the Nova Pro Knowledge Base Client.

Requirements: 5.4, 5.5, 5.10
"""

import asyncio
import json
import time
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum
import re
try:
    import structlog
    logger = structlog.get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

try:
    from .nova_pro_knowledge_base_client import (
        NovaProKnowledgeBaseClient,
        QueryResult,
        MBTITraits,
        QueryStrategy
    )
    from ..models.tourist_spot_models import TouristSpot
except ImportError:
    # For testing purposes, create minimal classes
    class NovaProKnowledgeBaseClient:
        def __init__(self):
            self.mbti_traits_map = {}
    
    class QueryResult:
        pass
    
    class MBTITraits:
        pass
    
    class QueryStrategy:
        pass
    
    class TouristSpot:
        pass


class PersonalityDimension(Enum):
    """MBTI personality dimensions."""
    ENERGY_SOURCE = "energy_source"  # E/I
    INFORMATION_PROCESSING = "information_processing"  # S/N
    DECISION_MAKING = "decision_making"  # T/F
    LIFESTYLE = "lifestyle"  # J/P


@dataclass
class PersonalityProfile:
    """Complete MBTI personality profile with matching preferences."""
    mbti_type: str
    dimensions: Dict[PersonalityDimension, str]
    traits: MBTITraits
    matching_score_weights: Dict[str, float]
    preferred_query_strategies: List[QueryStrategy]
    optimization_notes: Dict[str, Any]


@dataclass
class MatchingResult:
    """Result of MBTI personality matching for tourist spots."""
    tourist_spot: TouristSpot
    mbti_match_score: float
    matching_reasons: List[str]
    personality_alignment: Dict[str, float]
    recommendation_confidence: float


class MBTIPersonalityProcessor:
    """MBTI personality processing service with advanced matching logic.
    
    This service provides MBTI personality validation, trait mapping, and
    personality-specific tourist spot matching. It implements fast query
    optimization strategies and integrates with Nova Pro Knowledge Base Client
    for efficient tourist spot retrieval.
    
    Attributes:
        nova_client: Nova Pro Knowledge Base Client instance
        personality_profiles: Mapping of MBTI types to personality profiles
        matching_cache: Cache for personality matching results
        performance_metrics: Performance tracking for optimization
    """
    
    def __init__(
        self,
        nova_client: Optional[NovaProKnowledgeBaseClient] = None,
        enable_caching: bool = True
    ):
        """Initialize MBTI Personality Processor.
        
        Args:
            nova_client: Nova Pro Knowledge Base Client (creates new if None)
            enable_caching: Whether to enable result caching
        """
        self.nova_client = nova_client or NovaProKnowledgeBaseClient()
        self.enable_caching = enable_caching
        
        # Initialize personality profiles
        self.personality_profiles: Dict[str, PersonalityProfile] = {}
        self._initialize_personality_profiles()
        
        # Caching and performance tracking
        self.matching_cache: Dict[str, List[MatchingResult]] = {}
        self.performance_metrics: Dict[str, Any] = {}
        
        logger.info(
            "MBTI Personality Processor initialized",
            profiles_loaded=len(self.personality_profiles),
            caching_enabled=enable_caching
        )
    
    def _initialize_personality_profiles(self) -> None:
        """Initialize comprehensive MBTI personality profiles."""
        
        # Define all 16 MBTI types with detailed profiles
        mbti_definitions = {
            'INFJ': {
                'dimensions': {
                    PersonalityDimension.ENERGY_SOURCE: 'Introversion',
                    PersonalityDimension.INFORMATION_PROCESSING: 'Intuition',
                    PersonalityDimension.DECISION_MAKING: 'Feeling',
                    PersonalityDimension.LIFESTYLE: 'Judging'
                },
                'matching_weights': {
                    'cultural_significance': 0.9,
                    'peaceful_environment': 0.8,
                    'intellectual_stimulation': 0.8,
                    'crowd_level': 0.7,
                    'authenticity': 0.8
                },
                'preferred_strategies': [
                    QueryStrategy.SPECIFIC_TRAITS,
                    QueryStrategy.CATEGORY_BASED,
                    QueryStrategy.BROAD_PERSONALITY
                ],
                'optimization_notes': {
                    'best_performing_categories': ['cultural_sites', 'museums', 'quiet_spaces'],
                    'recommended_query_count': 12,
                    'response_time_target': 3.0
                }
            },
            'ENFP': {
                'dimensions': {
                    PersonalityDimension.ENERGY_SOURCE: 'Extraversion',
                    PersonalityDimension.INFORMATION_PROCESSING: 'Intuition',
                    PersonalityDimension.DECISION_MAKING: 'Feeling',
                    PersonalityDimension.LIFESTYLE: 'Perceiving'
                },
                'matching_weights': {
                    'social_interaction': 0.9,
                    'variety_options': 0.8,
                    'spontaneity_support': 0.8,
                    'energy_level': 0.7,
                    'inspiration_factor': 0.8
                },
                'preferred_strategies': [
                    QueryStrategy.BROAD_PERSONALITY,
                    QueryStrategy.CATEGORY_BASED,
                    QueryStrategy.LOCATION_FOCUSED
                ],
                'optimization_notes': {
                    'best_performing_categories': ['markets', 'festivals', 'interactive_venues'],
                    'recommended_query_count': 15,
                    'response_time_target': 2.5
                }
            },
            'INTJ': {
                'dimensions': {
                    PersonalityDimension.ENERGY_SOURCE: 'Introversion',
                    PersonalityDimension.INFORMATION_PROCESSING: 'Intuition',
                    PersonalityDimension.DECISION_MAKING: 'Thinking',
                    PersonalityDimension.LIFESTYLE: 'Judging'
                },
                'matching_weights': {
                    'strategic_value': 0.9,
                    'educational_content': 0.8,
                    'architectural_significance': 0.8,
                    'efficiency_access': 0.7,
                    'comprehensive_information': 0.8
                },
                'preferred_strategies': [
                    QueryStrategy.SPECIFIC_TRAITS,
                    QueryStrategy.CATEGORY_BASED,
                    QueryStrategy.LOCATION_FOCUSED
                ],
                'optimization_notes': {
                    'best_performing_categories': ['museums', 'architecture', 'technology_centers'],
                    'recommended_query_count': 10,
                    'response_time_target': 2.0
                }
            },
            'ESTP': {
                'dimensions': {
                    PersonalityDimension.ENERGY_SOURCE: 'Extraversion',
                    PersonalityDimension.INFORMATION_PROCESSING: 'Sensing',
                    PersonalityDimension.DECISION_MAKING: 'Thinking',
                    PersonalityDimension.LIFESTYLE: 'Perceiving'
                },
                'matching_weights': {
                    'activity_level': 0.9,
                    'immediate_gratification': 0.8,
                    'physical_engagement': 0.8,
                    'social_energy': 0.7,
                    'variety_excitement': 0.8
                },
                'preferred_strategies': [
                    QueryStrategy.CATEGORY_BASED,
                    QueryStrategy.BROAD_PERSONALITY,
                    QueryStrategy.LOCATION_FOCUSED
                ],
                'optimization_notes': {
                    'best_performing_categories': ['outdoor_activities', 'sports_venues', 'entertainment'],
                    'recommended_query_count': 18,
                    'response_time_target': 3.5
                }
            }
        }
        
        # Create personality profiles for defined types
        for mbti_type, definition in mbti_definitions.items():
            traits = self.nova_client.mbti_traits_map.get(mbti_type)
            if traits:
                profile = PersonalityProfile(
                    mbti_type=mbti_type,
                    dimensions=definition['dimensions'],
                    traits=traits,
                    matching_score_weights=definition['matching_weights'],
                    preferred_query_strategies=definition['preferred_strategies'],
                    optimization_notes=definition['optimization_notes']
                )
                self.personality_profiles[mbti_type] = profile
        
        # Generate profiles for remaining MBTI types
        all_mbti_types = [
            'INTJ', 'INTP', 'ENTJ', 'ENTP',
            'INFJ', 'INFP', 'ENFJ', 'ENFP',
            'ISTJ', 'ISFJ', 'ESTJ', 'ESFJ',
            'ISTP', 'ISFP', 'ESTP', 'ESFP'
        ]
        
        for mbti_type in all_mbti_types:
            if mbti_type not in self.personality_profiles:
                self.personality_profiles[mbti_type] = self._generate_basic_profile(mbti_type)
    
    def _generate_basic_profile(self, mbti_type: str) -> PersonalityProfile:
        """Generate basic personality profile for MBTI types not explicitly defined.
        
        Args:
            mbti_type: 4-character MBTI code
            
        Returns:
            PersonalityProfile with basic characteristics
        """
        # Extract dimensions from MBTI code
        dimensions = {
            PersonalityDimension.ENERGY_SOURCE: 'Extraversion' if mbti_type[0] == 'E' else 'Introversion',
            PersonalityDimension.INFORMATION_PROCESSING: 'Intuition' if mbti_type[1] == 'N' else 'Sensing',
            PersonalityDimension.DECISION_MAKING: 'Feeling' if mbti_type[2] == 'F' else 'Thinking',
            PersonalityDimension.LIFESTYLE: 'Judging' if mbti_type[3] == 'J' else 'Perceiving'
        }
        
        # Basic matching weights
        matching_weights = {
            'general_appeal': 0.7,
            'accessibility': 0.6,
            'variety': 0.6,
            'comfort_level': 0.5
        }
        
        # Default strategies
        preferred_strategies = [
            QueryStrategy.BROAD_PERSONALITY,
            QueryStrategy.CATEGORY_BASED
        ]
        
        # Basic optimization notes
        optimization_notes = {
            'best_performing_categories': ['general_attractions'],
            'recommended_query_count': 10,
            'response_time_target': 3.0
        }
        
        traits = self.nova_client.mbti_traits_map.get(mbti_type)
        
        return PersonalityProfile(
            mbti_type=mbti_type,
            dimensions=dimensions,
            traits=traits,
            matching_score_weights=matching_weights,
            preferred_query_strategies=preferred_strategies,
            optimization_notes=optimization_notes
        )
    
    def validate_mbti_personality(self, mbti_personality: str) -> Tuple[bool, str]:
        """Validate MBTI personality format and return normalized version.
        
        Args:
            mbti_personality: MBTI personality string to validate
            
        Returns:
            Tuple of (is_valid, normalized_mbti_type)
        """
        if not mbti_personality or not isinstance(mbti_personality, str):
            return False, ""
        
        # Clean and normalize
        mbti_clean = re.sub(r'[^A-Za-z]', '', mbti_personality).upper()
        
        if len(mbti_clean) != 4:
            return False, ""
        
        # Validate each position
        valid_positions = [
            ['E', 'I'],  # Energy source
            ['S', 'N'],  # Information processing
            ['T', 'F'],  # Decision making
            ['J', 'P']   # Lifestyle
        ]
        
        for i, char in enumerate(mbti_clean):
            if char not in valid_positions[i]:
                return False, ""
        
        return True, mbti_clean
    
    def get_personality_traits(self, mbti_personality: str) -> Optional[MBTITraits]:
        """Get personality traits for specific MBTI type.
        
        Args:
            mbti_personality: 4-character MBTI code
            
        Returns:
            MBTITraits object or None if not found
        """
        is_valid, normalized_mbti = self.validate_mbti_personality(mbti_personality)
        if not is_valid:
            return None
        
        profile = self.personality_profiles.get(normalized_mbti)
        return profile.traits if profile else None
    
    def get_personality_profile(self, mbti_personality: str) -> Optional[PersonalityProfile]:
        """Get complete personality profile for specific MBTI type.
        
        Args:
            mbti_personality: 4-character MBTI code
            
        Returns:
            PersonalityProfile object or None if not found
        """
        is_valid, normalized_mbti = self.validate_mbti_personality(mbti_personality)
        if not is_valid:
            return None
        
        return self.personality_profiles.get(normalized_mbti)
    
    async def find_personality_matched_spots(
        self,
        mbti_personality: str,
        max_results: int = 50,
        use_cache: bool = True,
        apply_advanced_matching: bool = True
    ) -> List[MatchingResult]:
        """Find tourist spots matched to specific MBTI personality.
        
        Args:
            mbti_personality: 4-character MBTI code
            max_results: Maximum number of results to return
            use_cache: Whether to use cached results
            apply_advanced_matching: Whether to apply advanced matching logic
            
        Returns:
            List of MatchingResult objects with scored tourist spots
            
        Raises:
            ValueError: If MBTI personality format is invalid
        """
        start_time = time.time()
        
        # Validate MBTI personality
        is_valid, normalized_mbti = self.validate_mbti_personality(mbti_personality)
        if not is_valid:
            raise ValueError(
                f"Invalid MBTI personality format: '{mbti_personality}'. "
                "Expected 4-character code like INFJ, ENFP."
            )
        
        cache_key = f"{normalized_mbti}_{max_results}_{apply_advanced_matching}"
        
        # Check cache
        if use_cache and self.enable_caching and cache_key in self.matching_cache:
            logger.info(
                "Returning cached personality matching results",
                mbti_type=normalized_mbti,
                cached_results=len(self.matching_cache[cache_key])
            )
            return self.matching_cache[cache_key][:max_results]
        
        logger.info(
            "Starting personality-matched tourist spot search",
            mbti_type=normalized_mbti,
            max_results=max_results,
            advanced_matching=apply_advanced_matching
        )
        
        # Get personality profile
        profile = self.get_personality_profile(normalized_mbti)
        if not profile:
            raise ValueError(f"No personality profile found for MBTI type: {normalized_mbti}")
        
        # Query knowledge base using Nova Pro client
        query_results = await self.nova_client.query_mbti_tourist_spots(
            normalized_mbti,
            use_cache=use_cache,
            max_total_results=max_results * 2  # Get more for better filtering
        )
        
        # Apply personality matching logic
        matching_results = []
        
        for query_result in query_results:
            if apply_advanced_matching:
                matching_result = self._apply_advanced_personality_matching(
                    query_result,
                    profile
                )
            else:
                matching_result = self._apply_basic_personality_matching(
                    query_result,
                    profile
                )
            
            if matching_result:
                matching_results.append(matching_result)
        
        # Sort by matching score and confidence
        matching_results.sort(
            key=lambda x: (x.mbti_match_score, x.recommendation_confidence),
            reverse=True
        )
        
        # Limit results
        final_results = matching_results[:max_results]
        
        # Cache results
        if use_cache and self.enable_caching:
            self.matching_cache[cache_key] = final_results
        
        # Update performance metrics
        execution_time = time.time() - start_time
        self.performance_metrics[normalized_mbti] = {
            'execution_time': execution_time,
            'query_results_count': len(query_results),
            'matching_results_count': len(final_results),
            'advanced_matching_used': apply_advanced_matching,
            'timestamp': time.time()
        }
        
        logger.info(
            "Personality matching completed",
            mbti_type=normalized_mbti,
            execution_time=f"{execution_time:.2f}s",
            query_results=len(query_results),
            matching_results=len(final_results)
        )
        
        return final_results
    
    def _apply_advanced_personality_matching(
        self,
        query_result: QueryResult,
        profile: PersonalityProfile
    ) -> Optional[MatchingResult]:
        """Apply advanced personality matching logic to tourist spot.
        
        Args:
            query_result: Query result from Nova Pro client
            profile: MBTI personality profile
            
        Returns:
            MatchingResult object or None if not suitable
        """
        tourist_spot = query_result.tourist_spot
        
        # Initialize scoring components
        base_score = query_result.relevance_score
        personality_scores = {}
        matching_reasons = []
        
        # Score based on personality dimensions
        if profile.traits:
            # Energy source matching
            if profile.dimensions[PersonalityDimension.ENERGY_SOURCE] == 'Introversion':
                # Prefer quieter, less crowded attractions
                if any(keyword in tourist_spot.description.lower() for keyword in 
                       ['quiet', 'peaceful', 'serene', 'contemplative']):
                    personality_scores['energy_match'] = 0.8
                    matching_reasons.append("Suitable for introverted preferences")
                else:
                    personality_scores['energy_match'] = 0.4
            else:
                # Prefer social, energetic attractions
                if any(keyword in tourist_spot.description.lower() for keyword in 
                       ['vibrant', 'lively', 'social', 'interactive']):
                    personality_scores['energy_match'] = 0.8
                    matching_reasons.append("Suitable for extraverted preferences")
                else:
                    personality_scores['energy_match'] = 0.4
            
            # Information processing matching
            if profile.dimensions[PersonalityDimension.INFORMATION_PROCESSING] == 'Intuition':
                # Prefer conceptual, creative, future-oriented attractions
                if any(keyword in tourist_spot.description.lower() for keyword in 
                       ['art', 'creative', 'innovative', 'cultural', 'conceptual']):
                    personality_scores['info_processing_match'] = 0.8
                    matching_reasons.append("Appeals to intuitive information processing")
                else:
                    personality_scores['info_processing_match'] = 0.5
            else:
                # Prefer concrete, practical, hands-on attractions
                if any(keyword in tourist_spot.description.lower() for keyword in 
                       ['hands-on', 'practical', 'traditional', 'historical', 'concrete']):
                    personality_scores['info_processing_match'] = 0.8
                    matching_reasons.append("Appeals to sensing information processing")
                else:
                    personality_scores['info_processing_match'] = 0.5
            
            # Decision making matching
            if profile.dimensions[PersonalityDimension.DECISION_MAKING] == 'Feeling':
                # Prefer people-centered, value-based attractions
                if any(keyword in tourist_spot.description.lower() for keyword in 
                       ['cultural', 'community', 'heritage', 'meaningful', 'personal']):
                    personality_scores['decision_match'] = 0.8
                    matching_reasons.append("Aligns with feeling-based decision making")
                else:
                    personality_scores['decision_match'] = 0.5
            else:
                # Prefer logical, analytical attractions
                if any(keyword in tourist_spot.description.lower() for keyword in 
                       ['technical', 'analytical', 'systematic', 'logical', 'scientific']):
                    personality_scores['decision_match'] = 0.8
                    matching_reasons.append("Aligns with thinking-based decision making")
                else:
                    personality_scores['decision_match'] = 0.5
            
            # Lifestyle matching
            if profile.dimensions[PersonalityDimension.LIFESTYLE] == 'Judging':
                # Prefer structured, planned attractions with clear schedules
                if tourist_spot.operating_hours and any(
                    getattr(tourist_spot.operating_hours, day) for day in 
                    ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
                ):
                    personality_scores['lifestyle_match'] = 0.7
                    matching_reasons.append("Suitable for structured planning preferences")
                else:
                    personality_scores['lifestyle_match'] = 0.4
            else:
                # Prefer flexible, spontaneous attractions
                personality_scores['lifestyle_match'] = 0.6
                matching_reasons.append("Allows for flexible exploration")
        
        # Calculate weighted personality alignment
        personality_alignment = {}
        total_weight = 0
        weighted_score = 0
        
        for score_type, score in personality_scores.items():
            weight = profile.matching_score_weights.get(score_type, 0.5)
            personality_alignment[score_type] = score
            weighted_score += score * weight
            total_weight += weight
        
        if total_weight > 0:
            weighted_score /= total_weight
        
        # Combine base relevance score with personality matching
        final_mbti_score = (base_score * 0.4) + (weighted_score * 0.6)
        
        # Calculate recommendation confidence
        confidence_factors = [
            base_score,
            weighted_score,
            len(matching_reasons) / 4.0,  # More reasons = higher confidence
            1.0 if tourist_spot.mbti_match else 0.5
        ]
        recommendation_confidence = sum(confidence_factors) / len(confidence_factors)
        
        # Filter out low-scoring matches
        if final_mbti_score < 0.3:
            return None
        
        return MatchingResult(
            tourist_spot=tourist_spot,
            mbti_match_score=final_mbti_score,
            matching_reasons=matching_reasons,
            personality_alignment=personality_alignment,
            recommendation_confidence=min(recommendation_confidence, 1.0)
        )
    
    def _apply_basic_personality_matching(
        self,
        query_result: QueryResult,
        profile: PersonalityProfile
    ) -> Optional[MatchingResult]:
        """Apply basic personality matching logic to tourist spot.
        
        Args:
            query_result: Query result from Nova Pro client
            profile: MBTI personality profile
            
        Returns:
            MatchingResult object or None if not suitable
        """
        tourist_spot = query_result.tourist_spot
        base_score = query_result.relevance_score
        
        # Simple matching based on MBTI match flag and relevance score
        mbti_match_bonus = 0.2 if tourist_spot.mbti_match else 0.0
        final_score = base_score + mbti_match_bonus
        
        matching_reasons = []
        if tourist_spot.mbti_match:
            matching_reasons.append(f"Specifically matched to {profile.mbti_type} personality")
        
        personality_alignment = {
            'basic_match': 1.0 if tourist_spot.mbti_match else 0.5
        }
        
        return MatchingResult(
            tourist_spot=tourist_spot,
            mbti_match_score=final_score,
            matching_reasons=matching_reasons,
            personality_alignment=personality_alignment,
            recommendation_confidence=base_score
        )
    
    def get_optimization_recommendations(self, mbti_personality: str) -> Dict[str, Any]:
        """Get query optimization recommendations for specific MBTI type.
        
        Args:
            mbti_personality: 4-character MBTI code
            
        Returns:
            Dictionary with optimization recommendations
        """
        is_valid, normalized_mbti = self.validate_mbti_personality(mbti_personality)
        if not is_valid:
            return {}
        
        profile = self.get_personality_profile(normalized_mbti)
        if not profile:
            return {}
        
        return {
            'mbti_type': normalized_mbti,
            'preferred_strategies': [strategy.value for strategy in profile.preferred_query_strategies],
            'optimization_notes': profile.optimization_notes,
            'matching_weights': profile.matching_score_weights,
            'recommended_max_results': profile.optimization_notes.get('recommended_query_count', 15),
            'target_response_time': profile.optimization_notes.get('response_time_target', 3.0)
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for personality processing.
        
        Returns:
            Dictionary with performance metrics by MBTI type
        """
        return {
            'processor_metrics': self.performance_metrics.copy(),
            'nova_client_metrics': self.nova_client.get_performance_metrics(),
            'cache_stats': self.get_cache_stats()
        }
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for personality matching.
        
        Returns:
            Dictionary with cache statistics
        """
        if not self.enable_caching:
            return {'caching_enabled': False}
        
        return {
            'caching_enabled': True,
            'cached_queries': len(self.matching_cache),
            'total_cached_results': sum(len(results) for results in self.matching_cache.values()),
            'cache_keys': list(self.matching_cache.keys())
        }
    
    def clear_cache(self) -> None:
        """Clear all caches."""
        self.matching_cache.clear()
        self.nova_client.clear_cache()
        logger.info("All caches cleared")
    
    def get_supported_mbti_types(self) -> List[str]:
        """Get list of supported MBTI personality types.
        
        Returns:
            List of supported 4-character MBTI codes
        """
        return sorted(list(self.personality_profiles.keys()))