"""
Orchestration Types

This module contains shared types and data classes used across the orchestration system
to avoid circular imports between modules.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, List
from datetime import datetime


class RequestType(Enum):
    """Types of user requests that can be orchestrated."""
    RESTAURANT_SEARCH_BY_LOCATION = "restaurant_search_by_location"
    RESTAURANT_SEARCH_BY_MEAL = "restaurant_search_by_meal"
    RESTAURANT_RECOMMENDATION = "restaurant_recommendation"
    COMBINED_SEARCH_AND_RECOMMENDATION = "combined_search_and_recommendation"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    UNKNOWN = "unknown"


class ExecutionStrategy(Enum):
    """Workflow execution strategies."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"


@dataclass
class UserContext:
    """User context for personalized tool selection."""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    mbti_type: Optional[str] = None
    conversation_history: List[str] = field(default_factory=list)
    preferences: Dict[str, Any] = field(default_factory=dict)
    location_context: Optional[str] = None


@dataclass
class Intent:
    """Analyzed user intent with extracted parameters."""
    type: RequestType
    confidence: float
    parameters: Dict[str, Any] = field(default_factory=dict)
    required_capabilities: List[str] = field(default_factory=list)
    optional_capabilities: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            'type': self.type.value,
            'confidence': self.confidence,
            'parameters': self.parameters,
            'required_capabilities': self.required_capabilities,
            'optional_capabilities': self.optional_capabilities
        }


@dataclass
class SelectedTool:
    """Tool selected for execution with metadata."""
    tool_id: str
    tool_name: str
    confidence: float
    expected_performance: Dict[str, float]
    fallback_tools: List[str] = field(default_factory=list)
    selection_reason: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        from dataclasses import asdict
        return asdict(self)


@dataclass
class OrchestrationResult:
    """Result of tool orchestration."""
    correlation_id: str
    success: bool
    results: List[Dict[str, Any]] = field(default_factory=list)
    execution_time_ms: float = 0.0
    tools_used: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    fallback_used: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        from dataclasses import asdict
        return asdict(self)