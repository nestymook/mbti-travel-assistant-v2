"""
Intent Analysis System

This module provides intelligent intent analysis for the MBTI Travel Planner Agent,
enabling accurate classification of user requests and extraction of relevant parameters.

Features:
- Request type classification using pattern matching and NLP techniques
- Parameter extraction for districts, meal types, and MBTI data
- Context-aware analysis using conversation history and user preferences
- Confidence scoring for intent classification
- Support for multiple intent types and complex requests
"""

import re
import logging
from typing import Dict, Any, Optional, List, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json

# Import shared types
from .orchestration_types import RequestType, Intent, UserContext


class ParameterType(Enum):
    """Types of parameters that can be extracted from user requests."""
    DISTRICT = "district"
    MEAL_TYPE = "meal_type"
    MBTI_TYPE = "mbti_type"
    CUISINE_TYPE = "cuisine_type"
    PRICE_RANGE = "price_range"
    GROUP_SIZE = "group_size"
    DIETARY_RESTRICTION = "dietary_restriction"
    OCCASION = "occasion"
    TIME_PREFERENCE = "time_preference"


@dataclass
class ExtractionPattern:
    """Pattern for extracting parameters from text."""
    parameter_type: ParameterType
    patterns: List[str]
    keywords: List[str]
    confidence_boost: float = 0.1
    
    def matches(self, text: str) -> List[str]:
        """Check if pattern matches text and return extracted values."""
        text_lower = text.lower()
        matches = []
        
        # Check regex patterns
        for pattern in self.patterns:
            regex_matches = re.findall(pattern, text_lower, re.IGNORECASE)
            matches.extend(regex_matches)
        
        # Check keyword matches
        for keyword in self.keywords:
            if keyword.lower() in text_lower:
                matches.append(keyword)
        
        return list(set(matches))  # Remove duplicates


@dataclass
class IntentClassificationRule:
    """Rule for classifying user intent."""
    intent_type: RequestType
    required_keywords: List[str]
    optional_keywords: List[str]
    negative_keywords: List[str]  # Keywords that reduce confidence
    base_confidence: float = 0.6
    keyword_weight: float = 0.3
    
    def calculate_confidence(self, text: str) -> float:
        """Calculate confidence score for this intent type."""
        text_lower = text.lower()
        
        # Check required keywords
        required_matches = sum(1 for keyword in self.required_keywords 
                             if keyword.lower() in text_lower)
        if self.required_keywords and required_matches == 0:
            return 0.0
        
        required_score = required_matches / len(self.required_keywords) if self.required_keywords else 1.0
        
        # Check optional keywords
        optional_matches = sum(1 for keyword in self.optional_keywords 
                             if keyword.lower() in text_lower)
        optional_score = optional_matches / len(self.optional_keywords) if self.optional_keywords else 0.0
        
        # Check negative keywords
        negative_matches = sum(1 for keyword in self.negative_keywords 
                             if keyword.lower() in text_lower)
        negative_penalty = negative_matches * 0.2
        
        # Calculate final confidence
        confidence = (
            self.base_confidence + 
            (required_score * self.keyword_weight) + 
            (optional_score * self.keyword_weight * 0.5) - 
            negative_penalty
        )
        
        return max(0.0, min(1.0, confidence))


class IntentAnalyzer:
    """
    Intelligent intent analyzer for user requests.
    
    This analyzer provides:
    - Request type classification using pattern matching
    - Parameter extraction for various data types
    - Context-aware analysis using user history
    - Confidence scoring for classification accuracy
    """
    
    def __init__(self, enable_context_analysis: bool = True):
        """
        Initialize the intent analyzer.
        
        Args:
            enable_context_analysis: Whether to use context for analysis
        """
        self.enable_context_analysis = enable_context_analysis
        self.logger = logging.getLogger(f"mbti_travel_planner.intent_analyzer")
        
        # Initialize classification rules
        self._classification_rules = self._initialize_classification_rules()
        
        # Initialize extraction patterns
        self._extraction_patterns = self._initialize_extraction_patterns()
        
        # Context analysis settings
        self._context_history_limit = 10
        self._context_confidence_boost = 0.15
        
        self.logger.info("Intent analyzer initialized")
    
    async def analyze_intent(self, 
                           request: str, 
                           context: Optional[UserContext] = None) -> Intent:
        """
        Analyze user request to determine intent and extract parameters.
        
        Args:
            request: User's request text
            context: Optional user context for personalization
            
        Returns:
            Intent object with analysis results
        """
        self.logger.debug(f"Analyzing intent for request: {request[:100]}...")
        
        # Step 1: Classify request type
        intent_type, base_confidence = self._classify_request_type(request)
        
        # Step 2: Extract parameters
        parameters = self._extract_parameters(request, intent_type)
        
        # Step 3: Determine required capabilities
        required_capabilities = self._get_required_capabilities(intent_type, parameters)
        optional_capabilities = self._get_optional_capabilities(intent_type, parameters)
        
        # Step 4: Apply context-aware analysis
        if self.enable_context_analysis and context:
            base_confidence = self._apply_context_analysis(
                request, intent_type, base_confidence, context
            )
            
            # Add context-based parameters
            context_params = self._extract_context_parameters(context)
            parameters.update(context_params)
        
        # Step 5: Create intent object
        intent = Intent(
            type=intent_type,
            confidence=base_confidence,
            parameters=parameters,
            required_capabilities=required_capabilities,
            optional_capabilities=optional_capabilities
        )
        
        self.logger.debug(f"Intent analysis complete", extra={
            'intent_type': intent_type.value,
            'confidence': base_confidence,
            'parameters_count': len(parameters),
            'required_capabilities': len(required_capabilities)
        })
        
        return intent
    
    def extract_parameters(self, request: str, intent: Intent) -> Dict[str, Any]:
        """
        Extract parameters from request text based on intent type.
        
        Args:
            request: User's request text
            intent: Classified intent
            
        Returns:
            Dictionary of extracted parameters
        """
        return self._extract_parameters(request, intent.type)
    
    def classify_request_type(self, request: str) -> RequestType:
        """
        Classify request type without full intent analysis.
        
        Args:
            request: User's request text
            
        Returns:
            Classified request type
        """
        intent_type, _ = self._classify_request_type(request)
        return intent_type
    
    def _initialize_classification_rules(self) -> List[IntentClassificationRule]:
        """Initialize intent classification rules."""
        return [
            # Restaurant search by location
            IntentClassificationRule(
                intent_type=RequestType.RESTAURANT_SEARCH_BY_LOCATION,
                required_keywords=["restaurant", "find", "search"],
                optional_keywords=[
                    "district", "area", "location", "central", "admiralty", 
                    "wan chai", "causeway bay", "tsim sha tsui", "mong kok",
                    "yau ma tei", "jordan", "sheung wan", "mid-levels"
                ],
                negative_keywords=["recommend", "best", "top", "suggest"],
                base_confidence=0.7,
                keyword_weight=0.25
            ),
            
            # Restaurant search by meal type
            IntentClassificationRule(
                intent_type=RequestType.RESTAURANT_SEARCH_BY_MEAL,
                required_keywords=["restaurant", "find", "search"],
                optional_keywords=[
                    "breakfast", "lunch", "dinner", "brunch", "meal",
                    "morning", "afternoon", "evening", "night"
                ],
                negative_keywords=["recommend", "best", "top", "suggest"],
                base_confidence=0.7,
                keyword_weight=0.25
            ),
            
            # Restaurant recommendation
            IntentClassificationRule(
                intent_type=RequestType.RESTAURANT_RECOMMENDATION,
                required_keywords=["recommend", "suggestion", "best", "top"],
                optional_keywords=[
                    "restaurant", "place", "good", "popular", "favorite",
                    "mbti", "personality", "type", "preference"
                ],
                negative_keywords=["search", "find", "all"],
                base_confidence=0.8,
                keyword_weight=0.2
            ),
            
            # Combined search and recommendation
            IntentClassificationRule(
                intent_type=RequestType.COMBINED_SEARCH_AND_RECOMMENDATION,
                required_keywords=["restaurant"],
                optional_keywords=[
                    "find", "search", "recommend", "best", "good",
                    "district", "area", "meal", "breakfast", "lunch", "dinner"
                ],
                negative_keywords=[],
                base_confidence=0.6,
                keyword_weight=0.2
            ),
            
            # Sentiment analysis
            IntentClassificationRule(
                intent_type=RequestType.SENTIMENT_ANALYSIS,
                required_keywords=["analyze", "sentiment", "review"],
                optional_keywords=[
                    "opinion", "feedback", "rating", "score", "evaluation"
                ],
                negative_keywords=["search", "find", "recommend"],
                base_confidence=0.8,
                keyword_weight=0.3
            )
        ]
    
    def _initialize_extraction_patterns(self) -> List[ExtractionPattern]:
        """Initialize parameter extraction patterns."""
        return [
            # District extraction
            ExtractionPattern(
                parameter_type=ParameterType.DISTRICT,
                patterns=[
                    r'\b(central|admiralty|wan chai|causeway bay|tsim sha tsui|mong kok|yau ma tei|jordan|sheung wan|mid-levels)\b',
                    r'\b(central district|admiralty district|wan chai district)\b'
                ],
                keywords=[
                    "Central", "Admiralty", "Wan Chai", "Causeway Bay", 
                    "Tsim Sha Tsui", "Mong Kok", "Yau Ma Tei", "Jordan", 
                    "Sheung Wan", "Mid-Levels"
                ],
                confidence_boost=0.2
            ),
            
            # Meal type extraction
            ExtractionPattern(
                parameter_type=ParameterType.MEAL_TYPE,
                patterns=[
                    r'\b(breakfast|lunch|dinner|brunch)\b',
                    r'\b(morning meal|afternoon meal|evening meal)\b'
                ],
                keywords=["breakfast", "lunch", "dinner", "brunch"],
                confidence_boost=0.15
            ),
            
            # MBTI type extraction
            ExtractionPattern(
                parameter_type=ParameterType.MBTI_TYPE,
                patterns=[
                    r'\b([IE][NS][FT][JP])\b',
                    r'\b(ENFP|ENFJ|INFP|INFJ|ENTP|ENTJ|INTP|INTJ|ESFP|ESFJ|ISFP|ISFJ|ESTP|ESTJ|ISTP|ISTJ)\b'
                ],
                keywords=[
                    "ENFP", "ENFJ", "INFP", "INFJ", "ENTP", "ENTJ", "INTP", "INTJ",
                    "ESFP", "ESFJ", "ISFP", "ISFJ", "ESTP", "ESTJ", "ISTP", "ISTJ"
                ],
                confidence_boost=0.25
            ),
            
            # Cuisine type extraction
            ExtractionPattern(
                parameter_type=ParameterType.CUISINE_TYPE,
                patterns=[
                    r'\b(chinese|cantonese|dim sum|italian|japanese|korean|thai|indian|western|fusion)\b'
                ],
                keywords=[
                    "Chinese", "Cantonese", "Dim Sum", "Italian", "Japanese", 
                    "Korean", "Thai", "Indian", "Western", "Fusion"
                ],
                confidence_boost=0.1
            ),
            
            # Price range extraction
            ExtractionPattern(
                parameter_type=ParameterType.PRICE_RANGE,
                patterns=[
                    r'\$+',  # $ symbols
                    r'\b(cheap|affordable|expensive|luxury|budget|high-end)\b',
                    r'\b(under \$?\d+|below \$?\d+|less than \$?\d+)\b'
                ],
                keywords=["cheap", "affordable", "expensive", "luxury", "budget", "high-end"],
                confidence_boost=0.1
            ),
            
            # Group size extraction
            ExtractionPattern(
                parameter_type=ParameterType.GROUP_SIZE,
                patterns=[
                    r'\b(\d+)\s*(people|person|pax|guests?)\b',
                    r'\b(solo|alone|couple|family|group|large group)\b'
                ],
                keywords=["solo", "couple", "family", "group"],
                confidence_boost=0.1
            )
        ]
    
    def _classify_request_type(self, request: str) -> Tuple[RequestType, float]:
        """Classify request type and return confidence score."""
        best_intent = RequestType.UNKNOWN
        best_confidence = 0.0
        
        for rule in self._classification_rules:
            confidence = rule.calculate_confidence(request)
            
            if confidence > best_confidence:
                best_confidence = confidence
                best_intent = rule.intent_type
        
        # If no rule matches well, try to infer from keywords
        if best_confidence < 0.5:
            best_intent, best_confidence = self._fallback_classification(request)
        
        return best_intent, best_confidence
    
    def _fallback_classification(self, request: str) -> Tuple[RequestType, float]:
        """Fallback classification when rules don't match well."""
        request_lower = request.lower()
        
        # Simple keyword-based fallback
        if any(word in request_lower for word in ["search", "find"]):
            if any(word in request_lower for word in ["district", "area", "location"]):
                return RequestType.RESTAURANT_SEARCH_BY_LOCATION, 0.4
            elif any(word in request_lower for word in ["breakfast", "lunch", "dinner"]):
                return RequestType.RESTAURANT_SEARCH_BY_MEAL, 0.4
            else:
                return RequestType.COMBINED_SEARCH_AND_RECOMMENDATION, 0.3
        
        elif any(word in request_lower for word in ["recommend", "best", "top"]):
            return RequestType.RESTAURANT_RECOMMENDATION, 0.4
        
        elif any(word in request_lower for word in ["analyze", "sentiment"]):
            return RequestType.SENTIMENT_ANALYSIS, 0.4
        
        return RequestType.UNKNOWN, 0.1
    
    def _extract_parameters(self, request: str, intent_type: RequestType) -> Dict[str, Any]:
        """Extract parameters from request text."""
        parameters = {}
        
        for pattern in self._extraction_patterns:
            matches = pattern.matches(request)
            
            if matches:
                param_name = pattern.parameter_type.value
                
                # Handle different parameter types
                if pattern.parameter_type == ParameterType.DISTRICT:
                    # Normalize district names
                    normalized_districts = [self._normalize_district_name(match) for match in matches]
                    parameters['districts'] = list(set(normalized_districts))
                
                elif pattern.parameter_type == ParameterType.MEAL_TYPE:
                    # Normalize meal types
                    normalized_meals = [self._normalize_meal_type(match) for match in matches]
                    parameters['meal_types'] = list(set(normalized_meals))
                
                elif pattern.parameter_type == ParameterType.MBTI_TYPE:
                    # Take the first valid MBTI type found
                    mbti_type = matches[0].upper()
                    if self._is_valid_mbti_type(mbti_type):
                        parameters['mbti_type'] = mbti_type
                
                else:
                    # For other parameter types, store as-is
                    if len(matches) == 1:
                        parameters[param_name] = matches[0]
                    else:
                        parameters[param_name] = matches
        
        return parameters
    
    def _get_required_capabilities(self, intent_type: RequestType, parameters: Dict[str, Any]) -> List[str]:
        """Get required capabilities based on intent type and parameters."""
        capabilities = []
        
        if intent_type == RequestType.RESTAURANT_SEARCH_BY_LOCATION:
            if 'districts' in parameters:
                capabilities.append('search_by_district')
            else:
                capabilities.append('search_restaurants_combined')
        
        elif intent_type == RequestType.RESTAURANT_SEARCH_BY_MEAL:
            if 'meal_types' in parameters:
                capabilities.append('search_by_meal_type')
            else:
                capabilities.append('search_restaurants_combined')
        
        elif intent_type == RequestType.RESTAURANT_RECOMMENDATION:
            capabilities.append('recommend_restaurants')
        
        elif intent_type == RequestType.COMBINED_SEARCH_AND_RECOMMENDATION:
            capabilities.extend(['search_restaurants_combined', 'recommend_restaurants'])
        
        elif intent_type == RequestType.SENTIMENT_ANALYSIS:
            capabilities.append('analyze_restaurant_sentiment')
        
        return capabilities
    
    def _get_optional_capabilities(self, intent_type: RequestType, parameters: Dict[str, Any]) -> List[str]:
        """Get optional capabilities based on intent type and parameters."""
        capabilities = []
        
        # Add MBTI personalization if MBTI type is available
        if 'mbti_type' in parameters:
            capabilities.append('mbti_personalization')
        
        # Add cuisine filtering if cuisine type is specified
        if 'cuisine_type' in parameters:
            capabilities.append('cuisine_filtering')
        
        # Add price filtering if price range is specified
        if 'price_range' in parameters:
            capabilities.append('price_filtering')
        
        return capabilities
    
    def _apply_context_analysis(self, 
                               request: str,
                               intent_type: RequestType,
                               base_confidence: float,
                               context: UserContext) -> float:
        """Apply context-aware analysis to improve intent classification."""
        confidence_adjustment = 0.0
        
        # Analyze conversation history
        if context.conversation_history:
            recent_history = context.conversation_history[-self._context_history_limit:]
            
            # Check for similar requests in history
            similar_requests = sum(1 for hist_req in recent_history 
                                 if self._calculate_request_similarity(request, hist_req) > 0.7)
            
            if similar_requests > 0:
                confidence_adjustment += self._context_confidence_boost * 0.5
        
        # Use MBTI type for personalization
        if context.mbti_type and intent_type == RequestType.RESTAURANT_RECOMMENDATION:
            confidence_adjustment += self._context_confidence_boost * 0.3
        
        # Use location context
        if context.location_context and intent_type == RequestType.RESTAURANT_SEARCH_BY_LOCATION:
            confidence_adjustment += self._context_confidence_boost * 0.2
        
        # Apply user preferences
        if context.preferences:
            # Check if request aligns with known preferences
            preference_alignment = self._calculate_preference_alignment(request, context.preferences)
            confidence_adjustment += preference_alignment * self._context_confidence_boost
        
        return min(1.0, base_confidence + confidence_adjustment)
    
    def _extract_context_parameters(self, context: UserContext) -> Dict[str, Any]:
        """Extract parameters from user context."""
        parameters = {}
        
        if context.mbti_type:
            parameters['mbti_type'] = context.mbti_type
        
        if context.location_context:
            parameters['location_context'] = context.location_context
        
        if context.user_id:
            parameters['user_id'] = context.user_id
        
        if context.session_id:
            parameters['session_id'] = context.session_id
        
        return parameters
    
    def _normalize_district_name(self, district: str) -> str:
        """Normalize district name to standard format."""
        district_mapping = {
            'central': 'Central',
            'admiralty': 'Admiralty',
            'wan chai': 'Wan Chai',
            'causeway bay': 'Causeway Bay',
            'tsim sha tsui': 'Tsim Sha Tsui',
            'mong kok': 'Mong Kok',
            'yau ma tei': 'Yau Ma Tei',
            'jordan': 'Jordan',
            'sheung wan': 'Sheung Wan',
            'mid-levels': 'Mid-Levels'
        }
        
        return district_mapping.get(district.lower(), district.title())
    
    def _normalize_meal_type(self, meal: str) -> str:
        """Normalize meal type to standard format."""
        meal_mapping = {
            'breakfast': 'breakfast',
            'brunch': 'breakfast',
            'morning': 'breakfast',
            'lunch': 'lunch',
            'afternoon': 'lunch',
            'dinner': 'dinner',
            'evening': 'dinner',
            'night': 'dinner'
        }
        
        return meal_mapping.get(meal.lower(), meal.lower())
    
    def _is_valid_mbti_type(self, mbti_type: str) -> bool:
        """Check if MBTI type is valid."""
        if len(mbti_type) != 4:
            return False
        
        valid_types = {
            'ENFP', 'ENFJ', 'INFP', 'INFJ', 'ENTP', 'ENTJ', 'INTP', 'INTJ',
            'ESFP', 'ESFJ', 'ISFP', 'ISFJ', 'ESTP', 'ESTJ', 'ISTP', 'ISTJ'
        }
        
        return mbti_type.upper() in valid_types
    
    def _calculate_request_similarity(self, request1: str, request2: str) -> float:
        """Calculate similarity between two requests."""
        # Simple word-based similarity
        words1 = set(request1.lower().split())
        words2 = set(request2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union) if union else 0.0
    
    def _calculate_preference_alignment(self, request: str, preferences: Dict[str, Any]) -> float:
        """Calculate how well request aligns with user preferences."""
        alignment_score = 0.0
        
        request_lower = request.lower()
        
        # Check cuisine preferences
        if 'cuisine_types' in preferences:
            for cuisine in preferences['cuisine_types']:
                if cuisine.lower() in request_lower:
                    alignment_score += 0.2
        
        # Check district preferences
        if 'preferred_districts' in preferences:
            for district in preferences['preferred_districts']:
                if district.lower() in request_lower:
                    alignment_score += 0.2
        
        # Check meal preferences
        if 'meal_preferences' in preferences:
            for meal in preferences['meal_preferences']:
                if meal.lower() in request_lower:
                    alignment_score += 0.1
        
        return min(1.0, alignment_score)