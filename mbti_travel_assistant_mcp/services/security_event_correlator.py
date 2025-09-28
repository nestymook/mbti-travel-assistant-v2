"""
Security Event Correlator for MBTI Travel Assistant MCP.

This module provides advanced security event correlation, pattern detection,
and automated threat response for authentication and user activity monitoring.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from collections import defaultdict, deque
from enum import Enum
import hashlib
import ipaddress
import re
from threading import Lock, Timer

from services.auth_error_handler import SecurityEvent, SecurityEventType, ErrorSeverity
from services.audit_logger import AuditEvent, AuditEventType, get_audit_logger
from models.auth_models import UserContext


# Configure logging
logger = logging.getLogger(__name__)


class ThreatLevel(Enum):
    """Threat severity levels for security correlation."""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CorrelationRuleType(Enum):
    """Types of correlation rules for threat detection."""
    FREQUENCY_BASED = "frequency_based"
    PATTERN_BASED = "pattern_based"
    ANOMALY_BASED = "anomaly_based"
    BEHAVIORAL_BASED = "behavioral_based"
    GEOGRAPHIC_BASED = "geographic_based"


@dataclass
class ThreatPattern:
    """Detected threat pattern from security event correlation."""
    pattern_id: str
    pattern_type: CorrelationRuleType
    threat_level: ThreatLevel
    description: str
    indicators: List[str]
    affected_users: Set[str]
    affected_ips: Set[str]
    first_detected: str
    last_detected: str
    event_count: int
    confidence_score: float
    recommended_actions: List[str]


@dataclass
class CorrelationRule:
    """Security event correlation rule definition."""
    rule_id: str
    rule_type: CorrelationRuleType
    name: str
    description: str
    event_types: List[SecurityEventType]
    time_window_minutes: int
    threshold_count: int
    severity_threshold: ErrorSeverity
    enabled: bool = True


@dataclass
class SecurityIncident:
    """Security incident created from correlated events."""
    incident_id: str
    title: str
    description: str
    severity: ThreatLevel
    status: str
    created_at: str
    updated_at: str
    affected_users: List[str]
    affected_resources: List[str]
    source_events: List[str]
    threat_patterns: List[str]
    response_actions: List[str]
    assignee: Optional[str] = None


class SecurityEventCorrelator:
    """
    Advanced security event correlator for threat detection and incident response.
    
    Provides real-time correlation of security events, pattern detection,
    automated threat assessment, and incident creation for security monitoring.
    """
    
    def __init__(self, enable_real_time_correlation: bool = True,
                 enable_automated_response: bool = True,
                 correlation_window_minutes: int = 60,
                 max_events_in_memory: int = 10000):
        """
        Initialize security event correlator.
        
        Args:
            enable_real_time_correlation: Whether to enable real-time correlation
            enable_automated_response: Whether to enable automated responses
            correlation_window_minutes: Time window for event correlation
            max_events_in_memory: Maximum events to keep in memory
        """
        self.enable_real_time_correlation = enable_real_time_correlation
        self.enable_automated_response = enable_automated_response
        self.correlation_window_minutes = correlation_window_minutes
        self.max_events_in_memory = max_events_in_memory
        
        # Thread safety
        self._lock = Lock()
        
        # Event storage and correlation state
        self._recent_events = deque(maxlen=max_events_in_memory)
        self._threat_patterns = {}  # pattern_id -> ThreatPattern
        self._security_incidents = {}  # incident_id -> SecurityIncident
        self._correlation_rules = {}  # rule_id -> CorrelationRule
        
        # Tracking structures
        self._user_event_counts = defaultdict(lambda: defaultdict(int))  # user_id -> event_type -> count
        self._ip_event_counts = defaultdict(lambda: defaultdict(int))    # ip -> event_type -> count
        self._event_sequences = defaultdict(list)  # user_id -> [events]
        
        # Initialize correlation rules
        self._initialize_correlation_rules()
        
        # Start background correlation if enabled
        if self.enable_real_time_correlation:
            self._start_correlation_timer()
        
        # Get audit logger
        self.audit_logger = get_audit_logger()
        
        logger.info("Security event correlator initialized")
    
    def process_security_event(self, security_event: SecurityEvent) -> List[ThreatPattern]:
        """
        Process security event and perform correlation analysis.
        
        Args:
            security_event: Security event to process
            
        Returns:
            List of detected threat patterns
        """
        try:
            with self._lock:
                # Add event to recent events
                self._recent_events.append(security_event)
                
                # Update tracking structures
                self._update_event_tracking(security_event)
                
                # Perform real-time correlation if enabled
                detected_patterns = []
                if self.enable_real_time_correlation:
                    detected_patterns = self._correlate_events([security_event])
                
                # Log correlation results
                if detected_patterns:
                    logger.warning(f"Detected {len(detected_patterns)} threat patterns from security event")
                    
                    # Create incidents for high-severity patterns
                    for pattern in detected_patterns:
                        if pattern.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
                            self._create_security_incident(pattern)
                
                return detected_patterns
        
        except Exception as e:
            logger.error(f"Failed to process security event: {e}")
            return []
    
    def correlate_authentication_events(self, user_context: Optional[UserContext] = None,
                                      time_window_hours: int = 24) -> List[ThreatPattern]:
        """
        Correlate authentication events for specific user or global analysis.
        
        Args:
            user_context: Optional user context to focus correlation
            time_window_hours: Time window for correlation analysis
            
        Returns:
            List of detected threat patterns
        """
        try:
            with self._lock:
                # Filter events by time window
                cutoff_time = datetime.now(timezone.utc) - timedelta(hours=time_window_hours)
                
                relevant_events = []
                for event in self._recent_events:
                    event_time = datetime.fromisoformat(event.timestamp.replace('Z', '+00:00'))
                    if event_time > cutoff_time:
                        # Filter by user if specified
                        if user_context is None or event.user_id == user_context.user_id:
                            relevant_events.append(event)
                
                # Perform correlation analysis
                detected_patterns = self._correlate_events(relevant_events)
                
                logger.info(f"Correlated {len(relevant_events)} events, detected {len(detected_patterns)} patterns")
                
                return detected_patterns
        
        except Exception as e:
            logger.error(f"Failed to correlate authentication events: {e}")
            return []
    
    def detect_brute_force_attacks(self, time_window_minutes: int = 15,
                                 failure_threshold: int = 5) -> List[ThreatPattern]:
        """
        Detect brute force authentication attacks.
        
        Args:
            time_window_minutes: Time window for analysis
            failure_threshold: Number of failures to trigger detection
            
        Returns:
            List of detected brute force patterns
        """
        try:
            with self._lock:
                cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=time_window_minutes)
                
                # Count failed authentication attempts by IP
                ip_failures = defaultdict(list)
                
                for event in self._recent_events:
                    if (event.event_type == SecurityEventType.AUTHENTICATION_FAILURE and
                        event.client_ip and event.client_ip != 'unknown'):
                        
                        event_time = datetime.fromisoformat(event.timestamp.replace('Z', '+00:00'))
                        if event_time > cutoff_time:
                            ip_failures[event.client_ip].append(event)
                
                # Detect brute force patterns
                brute_force_patterns = []
                
                for client_ip, failures in ip_failures.items():
                    if len(failures) >= failure_threshold:
                        pattern = self._create_brute_force_pattern(client_ip, failures)
                        brute_force_patterns.append(pattern)
                        
                        # Store pattern
                        self._threat_patterns[pattern.pattern_id] = pattern
                
                return brute_force_patterns
        
        except Exception as e:
            logger.error(f"Failed to detect brute force attacks: {e}")
            return []
    
    def detect_anomalous_user_behavior(self, user_id: str,
                                     time_window_hours: int = 24) -> List[ThreatPattern]:
        """
        Detect anomalous user behavior patterns.
        
        Args:
            user_id: User ID to analyze
            time_window_hours: Time window for analysis
            
        Returns:
            List of detected anomaly patterns
        """
        try:
            with self._lock:
                cutoff_time = datetime.now(timezone.utc) - timedelta(hours=time_window_hours)
                
                # Get user events
                user_events = []
                for event in self._recent_events:
                    if (event.user_id == user_id and
                        datetime.fromisoformat(event.timestamp.replace('Z', '+00:00')) > cutoff_time):
                        user_events.append(event)
                
                if len(user_events) < 5:  # Need minimum events for analysis
                    return []
                
                # Analyze patterns
                anomaly_patterns = []
                
                # Check for unusual access times
                access_times = [
                    datetime.fromisoformat(event.timestamp.replace('Z', '+00:00')).hour
                    for event in user_events
                ]
                
                if self._is_unusual_access_pattern(access_times):
                    pattern = self._create_anomaly_pattern(
                        user_id, "unusual_access_times", user_events,
                        "User accessing system at unusual times"
                    )
                    anomaly_patterns.append(pattern)
                
                # Check for rapid successive logins from different IPs
                ip_changes = self._detect_rapid_ip_changes(user_events)
                if ip_changes:
                    pattern = self._create_anomaly_pattern(
                        user_id, "rapid_ip_changes", user_events,
                        "User rapidly changing IP addresses"
                    )
                    anomaly_patterns.append(pattern)
                
                # Store patterns
                for pattern in anomaly_patterns:
                    self._threat_patterns[pattern.pattern_id] = pattern
                
                return anomaly_patterns
        
        except Exception as e:
            logger.error(f"Failed to detect anomalous user behavior: {e}")
            return []
    
    def get_security_incidents(self, severity_filter: Optional[ThreatLevel] = None,
                             status_filter: Optional[str] = None,
                             limit: int = 100) -> List[SecurityIncident]:
        """
        Get security incidents with optional filtering.
        
        Args:
            severity_filter: Optional severity level filter
            status_filter: Optional status filter
            limit: Maximum number of incidents to return
            
        Returns:
            List of security incidents
        """
        try:
            with self._lock:
                incidents = list(self._security_incidents.values())
                
                # Apply filters
                if severity_filter:
                    incidents = [i for i in incidents if i.severity == severity_filter]
                
                if status_filter:
                    incidents = [i for i in incidents if i.status == status_filter]
                
                # Sort by creation time (newest first)
                incidents.sort(key=lambda x: x.created_at, reverse=True)
                
                return incidents[:limit]
        
        except Exception as e:
            logger.error(f"Failed to get security incidents: {e}")
            return []
    
    def get_threat_patterns(self, pattern_type: Optional[CorrelationRuleType] = None,
                          threat_level: Optional[ThreatLevel] = None,
                          limit: int = 50) -> List[ThreatPattern]:
        """
        Get detected threat patterns with optional filtering.
        
        Args:
            pattern_type: Optional pattern type filter
            threat_level: Optional threat level filter
            limit: Maximum number of patterns to return
            
        Returns:
            List of threat patterns
        """
        try:
            with self._lock:
                patterns = list(self._threat_patterns.values())
                
                # Apply filters
                if pattern_type:
                    patterns = [p for p in patterns if p.pattern_type == pattern_type]
                
                if threat_level:
                    patterns = [p for p in patterns if p.threat_level == threat_level]
                
                # Sort by threat level and confidence
                patterns.sort(key=lambda x: (x.threat_level.value, x.confidence_score), reverse=True)
                
                return patterns[:limit]
        
        except Exception as e:
            logger.error(f"Failed to get threat patterns: {e}")
            return []
    
    def _correlate_events(self, events: List[SecurityEvent]) -> List[ThreatPattern]:
        """Correlate security events using defined rules."""
        detected_patterns = []
        
        try:
            # Apply each correlation rule
            for rule in self._correlation_rules.values():
                if not rule.enabled:
                    continue
                
                # Filter events by rule criteria
                relevant_events = [
                    event for event in events
                    if (event.event_type in rule.event_types and
                        event.severity.value >= rule.severity_threshold.value)
                ]
                
                if len(relevant_events) >= rule.threshold_count:
                    pattern = self._apply_correlation_rule(rule, relevant_events)
                    if pattern:
                        detected_patterns.append(pattern)
                        self._threat_patterns[pattern.pattern_id] = pattern
        
        except Exception as e:
            logger.error(f"Failed to correlate events: {e}")
        
        return detected_patterns
    
    def _apply_correlation_rule(self, rule: CorrelationRule,
                              events: List[SecurityEvent]) -> Optional[ThreatPattern]:
        """Apply specific correlation rule to events."""
        try:
            if rule.rule_type == CorrelationRuleType.FREQUENCY_BASED:
                return self._apply_frequency_rule(rule, events)
            elif rule.rule_type == CorrelationRuleType.PATTERN_BASED:
                return self._apply_pattern_rule(rule, events)
            elif rule.rule_type == CorrelationRuleType.ANOMALY_BASED:
                return self._apply_anomaly_rule(rule, events)
            else:
                logger.warning(f"Unsupported correlation rule type: {rule.rule_type}")
                return None
        
        except Exception as e:
            logger.error(f"Failed to apply correlation rule {rule.rule_id}: {e}")
            return None
    
    def _apply_frequency_rule(self, rule: CorrelationRule,
                            events: List[SecurityEvent]) -> Optional[ThreatPattern]:
        """Apply frequency-based correlation rule."""
        if len(events) < rule.threshold_count:
            return None
        
        # Group events by source (IP, user, etc.)
        event_groups = defaultdict(list)
        for event in events:
            key = event.client_ip or event.user_id or 'unknown'
            event_groups[key].append(event)
        
        # Find groups that exceed threshold
        for source, source_events in event_groups.items():
            if len(source_events) >= rule.threshold_count:
                return ThreatPattern(
                    pattern_id=self._generate_pattern_id(),
                    pattern_type=rule.rule_type,
                    threat_level=self._calculate_threat_level(len(source_events), rule.threshold_count),
                    description=f"High frequency of {rule.name} from {source}",
                    indicators=[f"source:{source}", f"event_count:{len(source_events)}"],
                    affected_users={event.user_id for event in source_events if event.user_id},
                    affected_ips={event.client_ip for event in source_events if event.client_ip},
                    first_detected=min(event.timestamp for event in source_events),
                    last_detected=max(event.timestamp for event in source_events),
                    event_count=len(source_events),
                    confidence_score=min(0.95, len(source_events) / rule.threshold_count * 0.7),
                    recommended_actions=self._get_recommended_actions(rule.rule_type, source_events)
                )
        
        return None
    
    def _apply_pattern_rule(self, rule: CorrelationRule,
                          events: List[SecurityEvent]) -> Optional[ThreatPattern]:
        """Apply pattern-based correlation rule."""
        # Look for specific event sequences or patterns
        if rule.name == "authentication_escalation":
            return self._detect_authentication_escalation(events)
        elif rule.name == "token_manipulation":
            return self._detect_token_manipulation(events)
        
        return None
    
    def _apply_anomaly_rule(self, rule: CorrelationRule,
                          events: List[SecurityEvent]) -> Optional[ThreatPattern]:
        """Apply anomaly-based correlation rule."""
        # Detect statistical anomalies in event patterns
        if len(events) < 10:  # Need sufficient data for anomaly detection
            return None
        
        # Simple anomaly detection based on event timing
        timestamps = [
            datetime.fromisoformat(event.timestamp.replace('Z', '+00:00'))
            for event in events
        ]
        
        # Check for unusual clustering of events
        time_diffs = [
            (timestamps[i+1] - timestamps[i]).total_seconds()
            for i in range(len(timestamps) - 1)
        ]
        
        avg_diff = sum(time_diffs) / len(time_diffs)
        rapid_events = sum(1 for diff in time_diffs if diff < avg_diff * 0.1)
        
        if rapid_events > len(time_diffs) * 0.5:  # More than 50% are rapid
            return ThreatPattern(
                pattern_id=self._generate_pattern_id(),
                pattern_type=rule.rule_type,
                threat_level=ThreatLevel.MEDIUM,
                description="Anomalous rapid sequence of security events",
                indicators=[f"rapid_events:{rapid_events}", f"total_events:{len(events)}"],
                affected_users={event.user_id for event in events if event.user_id},
                affected_ips={event.client_ip for event in events if event.client_ip},
                first_detected=min(event.timestamp for event in events),
                last_detected=max(event.timestamp for event in events),
                event_count=len(events),
                confidence_score=0.6,
                recommended_actions=["investigate_user_activity", "review_system_logs"]
            )
        
        return None
    
    def _create_brute_force_pattern(self, client_ip: str,
                                  failures: List[SecurityEvent]) -> ThreatPattern:
        """Create brute force attack pattern."""
        return ThreatPattern(
            pattern_id=self._generate_pattern_id(),
            pattern_type=CorrelationRuleType.FREQUENCY_BASED,
            threat_level=ThreatLevel.HIGH,
            description=f"Brute force attack detected from IP {client_ip}",
            indicators=[f"source_ip:{client_ip}", f"failed_attempts:{len(failures)}"],
            affected_users={event.user_id for event in failures if event.user_id},
            affected_ips={client_ip},
            first_detected=min(event.timestamp for event in failures),
            last_detected=max(event.timestamp for event in failures),
            event_count=len(failures),
            confidence_score=0.9,
            recommended_actions=[
                "block_source_ip",
                "notify_security_team",
                "review_affected_accounts",
                "enable_additional_monitoring"
            ]
        )
    
    def _create_anomaly_pattern(self, user_id: str, anomaly_type: str,
                              events: List[SecurityEvent], description: str) -> ThreatPattern:
        """Create anomaly-based threat pattern."""
        return ThreatPattern(
            pattern_id=self._generate_pattern_id(),
            pattern_type=CorrelationRuleType.ANOMALY_BASED,
            threat_level=ThreatLevel.MEDIUM,
            description=description,
            indicators=[f"user_id:{user_id}", f"anomaly_type:{anomaly_type}"],
            affected_users={user_id},
            affected_ips={event.client_ip for event in events if event.client_ip},
            first_detected=min(event.timestamp for event in events),
            last_detected=max(event.timestamp for event in events),
            event_count=len(events),
            confidence_score=0.7,
            recommended_actions=[
                "verify_user_identity",
                "review_user_activity",
                "consider_additional_authentication"
            ]
        )
    
    def _create_security_incident(self, threat_pattern: ThreatPattern) -> SecurityIncident:
        """Create security incident from threat pattern."""
        incident_id = self._generate_incident_id()
        
        incident = SecurityIncident(
            incident_id=incident_id,
            title=f"Security Incident: {threat_pattern.description}",
            description=f"Threat pattern detected: {threat_pattern.description}",
            severity=threat_pattern.threat_level,
            status="open",
            created_at=datetime.now(timezone.utc).isoformat(),
            updated_at=datetime.now(timezone.utc).isoformat(),
            affected_users=list(threat_pattern.affected_users),
            affected_resources=[],  # Could be populated based on pattern
            source_events=[],  # Could be populated with event IDs
            threat_patterns=[threat_pattern.pattern_id],
            response_actions=threat_pattern.recommended_actions
        )
        
        self._security_incidents[incident_id] = incident
        
        # Log incident creation
        self.audit_logger.log_security_violation(
            violation_type="security_incident_created",
            user_context=None,
            request_context={'incident_id': incident_id},
            violation_details={
                'threat_pattern_id': threat_pattern.pattern_id,
                'severity': threat_pattern.threat_level.value,
                'affected_users': list(threat_pattern.affected_users),
                'affected_ips': list(threat_pattern.affected_ips)
            }
        )
        
        logger.critical(f"Security incident created: {incident_id} - {threat_pattern.description}")
        
        return incident
    
    def _update_event_tracking(self, security_event: SecurityEvent) -> None:
        """Update event tracking structures."""
        if security_event.user_id:
            self._user_event_counts[security_event.user_id][security_event.event_type] += 1
        
        if security_event.client_ip:
            self._ip_event_counts[security_event.client_ip][security_event.event_type] += 1
        
        if security_event.user_id:
            self._event_sequences[security_event.user_id].append(security_event)
            # Limit sequence length
            if len(self._event_sequences[security_event.user_id]) > 100:
                self._event_sequences[security_event.user_id] = \
                    self._event_sequences[security_event.user_id][-50:]
    
    def _initialize_correlation_rules(self) -> None:
        """Initialize default correlation rules."""
        rules = [
            CorrelationRule(
                rule_id="auth_failure_frequency",
                rule_type=CorrelationRuleType.FREQUENCY_BASED,
                name="authentication_failures",
                description="High frequency of authentication failures",
                event_types=[SecurityEventType.AUTHENTICATION_FAILURE],
                time_window_minutes=15,
                threshold_count=5,
                severity_threshold=ErrorSeverity.MEDIUM
            ),
            CorrelationRule(
                rule_id="token_validation_failures",
                rule_type=CorrelationRuleType.FREQUENCY_BASED,
                name="token_validation_failures",
                description="High frequency of token validation failures",
                event_types=[SecurityEventType.TOKEN_VALIDATION_FAILURE],
                time_window_minutes=10,
                threshold_count=10,
                severity_threshold=ErrorSeverity.MEDIUM
            ),
            CorrelationRule(
                rule_id="suspicious_activity_pattern",
                rule_type=CorrelationRuleType.PATTERN_BASED,
                name="suspicious_activity",
                description="Pattern of suspicious activities",
                event_types=[SecurityEventType.SUSPICIOUS_ACTIVITY],
                time_window_minutes=30,
                threshold_count=3,
                severity_threshold=ErrorSeverity.MEDIUM
            ),
            CorrelationRule(
                rule_id="rapid_event_anomaly",
                rule_type=CorrelationRuleType.ANOMALY_BASED,
                name="rapid_events",
                description="Anomalous rapid sequence of events",
                event_types=[
                    SecurityEventType.AUTHENTICATION_FAILURE,
                    SecurityEventType.TOKEN_VALIDATION_FAILURE,
                    SecurityEventType.UNAUTHORIZED_ACCESS_ATTEMPT
                ],
                time_window_minutes=5,
                threshold_count=10,
                severity_threshold=ErrorSeverity.LOW
            )
        ]
        
        for rule in rules:
            self._correlation_rules[rule.rule_id] = rule
    
    def _start_correlation_timer(self) -> None:
        """Start background correlation timer."""
        def run_correlation():
            try:
                # Run periodic correlation analysis
                self._run_periodic_correlation()
                
                # Schedule next run
                Timer(300, run_correlation).start()  # Run every 5 minutes
            
            except Exception as e:
                logger.error(f"Error in correlation timer: {e}")
        
        Timer(60, run_correlation).start()  # Start after 1 minute
    
    def _run_periodic_correlation(self) -> None:
        """Run periodic correlation analysis on recent events."""
        try:
            with self._lock:
                # Get events from last correlation window
                cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=self.correlation_window_minutes)
                
                recent_events = [
                    event for event in self._recent_events
                    if datetime.fromisoformat(event.timestamp.replace('Z', '+00:00')) > cutoff_time
                ]
                
                if recent_events:
                    detected_patterns = self._correlate_events(recent_events)
                    
                    if detected_patterns:
                        logger.info(f"Periodic correlation detected {len(detected_patterns)} threat patterns")
        
        except Exception as e:
            logger.error(f"Failed to run periodic correlation: {e}")
    
    def _is_unusual_access_pattern(self, access_hours: List[int]) -> bool:
        """Check if access hours represent unusual pattern."""
        # Define normal business hours (9 AM to 6 PM)
        business_hours = set(range(9, 18))
        
        unusual_hours = [hour for hour in access_hours if hour not in business_hours]
        
        # Consider unusual if more than 70% of access is outside business hours
        return len(unusual_hours) > len(access_hours) * 0.7
    
    def _detect_rapid_ip_changes(self, events: List[SecurityEvent]) -> bool:
        """Detect rapid IP address changes for user."""
        ips = [event.client_ip for event in events if event.client_ip and event.client_ip != 'unknown']
        
        if len(set(ips)) < 2:  # Need at least 2 different IPs
            return False
        
        # Check if IP changes happen within short time windows
        ip_changes = 0
        for i in range(1, len(events)):
            if (events[i].client_ip != events[i-1].client_ip and
                events[i].client_ip and events[i-1].client_ip):
                
                time_diff = (
                    datetime.fromisoformat(events[i].timestamp.replace('Z', '+00:00')) -
                    datetime.fromisoformat(events[i-1].timestamp.replace('Z', '+00:00'))
                ).total_seconds()
                
                if time_diff < 300:  # Less than 5 minutes
                    ip_changes += 1
        
        return ip_changes >= 2  # At least 2 rapid IP changes
    
    def _calculate_threat_level(self, event_count: int, threshold: int) -> ThreatLevel:
        """Calculate threat level based on event count and threshold."""
        ratio = event_count / threshold
        
        if ratio >= 5:
            return ThreatLevel.CRITICAL
        elif ratio >= 3:
            return ThreatLevel.HIGH
        elif ratio >= 2:
            return ThreatLevel.MEDIUM
        else:
            return ThreatLevel.LOW
    
    def _get_recommended_actions(self, rule_type: CorrelationRuleType,
                               events: List[SecurityEvent]) -> List[str]:
        """Get recommended actions based on rule type and events."""
        base_actions = ["investigate_further", "review_logs"]
        
        if rule_type == CorrelationRuleType.FREQUENCY_BASED:
            base_actions.extend(["consider_rate_limiting", "block_if_malicious"])
        elif rule_type == CorrelationRuleType.PATTERN_BASED:
            base_actions.extend(["analyze_attack_pattern", "update_detection_rules"])
        elif rule_type == CorrelationRuleType.ANOMALY_BASED:
            base_actions.extend(["verify_user_behavior", "check_account_compromise"])
        
        # Add specific actions based on event types
        event_types = {event.event_type for event in events}
        
        if SecurityEventType.AUTHENTICATION_FAILURE in event_types:
            base_actions.append("review_authentication_logs")
        
        if SecurityEventType.SUSPICIOUS_ACTIVITY in event_types:
            base_actions.append("enhance_monitoring")
        
        return list(set(base_actions))  # Remove duplicates
    
    def _generate_pattern_id(self) -> str:
        """Generate unique pattern ID."""
        timestamp = datetime.now(timezone.utc).isoformat()
        return hashlib.md5(f"pattern_{timestamp}_{id(self)}".encode()).hexdigest()[:16]
    
    def _generate_incident_id(self) -> str:
        """Generate unique incident ID."""
        timestamp = datetime.now(timezone.utc).isoformat()
        return f"INC-{hashlib.md5(f'incident_{timestamp}_{id(self)}'.encode()).hexdigest()[:12].upper()}"


# Global correlator instance
_security_correlator = None
_correlator_lock = Lock()


def get_security_correlator() -> SecurityEventCorrelator:
    """Get global security event correlator instance."""
    global _security_correlator
    
    with _correlator_lock:
        if _security_correlator is None:
            _security_correlator = SecurityEventCorrelator()
        
        return _security_correlator


# Export main classes
__all__ = [
    'SecurityEventCorrelator',
    'ThreatPattern',
    'ThreatLevel',
    'CorrelationRule',
    'CorrelationRuleType',
    'SecurityIncident',
    'get_security_correlator'
]