"""
Error analysis and troubleshooting utilities for enhanced MCP status check system.

This service provides comprehensive error analysis, pattern detection,
and automated troubleshooting recommendations.
"""

import asyncio
import json
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
import statistics
import re

from models.error_models import (
    ErrorDetails, ErrorSeverity, ErrorCategory, ErrorCode, ErrorSummary
)
from models.logging_models import LogLevel, LogCategory


@dataclass
class ErrorPattern:
    """Represents a detected error pattern."""
    pattern_id: str
    pattern_type: str  # "frequency", "sequence", "correlation", "temporal"
    description: str
    error_codes: List[ErrorCode]
    servers_affected: List[str]
    frequency: int
    first_occurrence: datetime
    last_occurrence: datetime
    severity_distribution: Dict[str, int]
    confidence_score: float  # 0.0 to 1.0
    root_cause_hypothesis: Optional[str] = None
    recommended_actions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "pattern_id": self.pattern_id,
            "pattern_type": self.pattern_type,
            "description": self.description,
            "error_codes": [code.value for code in self.error_codes],
            "servers_affected": self.servers_affected,
            "frequency": self.frequency,
            "first_occurrence": self.first_occurrence.isoformat(),
            "last_occurrence": self.last_occurrence.isoformat(),
            "severity_distribution": self.severity_distribution,
            "confidence_score": self.confidence_score,
            "root_cause_hypothesis": self.root_cause_hypothesis,
            "recommended_actions": self.recommended_actions
        }


@dataclass
class TroubleshootingRecommendation:
    """Represents a troubleshooting recommendation."""
    recommendation_id: str
    title: str
    description: str
    priority: str  # "high", "medium", "low"
    category: str  # "immediate", "preventive", "monitoring"
    steps: List[str]
    expected_outcome: str
    estimated_time_minutes: int
    requires_restart: bool = False
    affects_availability: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "recommendation_id": self.recommendation_id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "category": self.category,
            "steps": self.steps,
            "expected_outcome": self.expected_outcome,
            "estimated_time_minutes": self.estimated_time_minutes,
            "requires_restart": self.requires_restart,
            "affects_availability": self.affects_availability
        }


@dataclass
class SystemHealthAssessment:
    """Comprehensive system health assessment."""
    assessment_id: str
    timestamp: datetime
    overall_health_score: float  # 0.0 to 1.0
    critical_issues: List[str]
    warnings: List[str]
    recommendations: List[TroubleshootingRecommendation]
    error_patterns: List[ErrorPattern]
    server_health_scores: Dict[str, float]
    trend_analysis: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "assessment_id": self.assessment_id,
            "timestamp": self.timestamp.isoformat(),
            "overall_health_score": self.overall_health_score,
            "critical_issues": self.critical_issues,
            "warnings": self.warnings,
            "recommendations": [r.to_dict() for r in self.recommendations],
            "error_patterns": [p.to_dict() for p in self.error_patterns],
            "server_health_scores": self.server_health_scores,
            "trend_analysis": self.trend_analysis
        }


class ErrorAnalyzer:
    """Comprehensive error analyzer for dual monitoring operations."""
    
    def __init__(self):
        """Initialize error analyzer."""
        self.error_history: List[ErrorDetails] = []
        self.pattern_cache: Dict[str, ErrorPattern] = {}
        self.analysis_cache: Dict[str, Any] = {}
        self.troubleshooting_rules: Dict[str, List[TroubleshootingRecommendation]] = {}
        
        # Initialize troubleshooting rules
        self._initialize_troubleshooting_rules()
    
    def add_error(self, error: ErrorDetails):
        """Add error to analysis history."""
        self.error_history.append(error)
        
        # Clear relevant caches
        self._clear_analysis_cache()
    
    def analyze_error_patterns(self, time_window_hours: int = 24) -> List[ErrorPattern]:
        """Analyze error patterns within time window."""
        cutoff_time = datetime.utcnow() - timedelta(hours=time_window_hours)
        recent_errors = [e for e in self.error_history if e.timestamp >= cutoff_time]
        
        if not recent_errors:
            return []
        
        patterns = []
        
        # Detect frequency patterns
        patterns.extend(self._detect_frequency_patterns(recent_errors))
        
        # Detect sequence patterns
        patterns.extend(self._detect_sequence_patterns(recent_errors))
        
        # Detect correlation patterns
        patterns.extend(self._detect_correlation_patterns(recent_errors))
        
        # Detect temporal patterns
        patterns.extend(self._detect_temporal_patterns(recent_errors))
        
        return patterns
    
    def generate_troubleshooting_recommendations(self, errors: List[ErrorDetails]) -> List[TroubleshootingRecommendation]:
        """Generate troubleshooting recommendations based on errors."""
        recommendations = []
        
        # Group errors by category and code
        error_groups = self._group_errors(errors)
        
        for (category, code), error_list in error_groups.items():
            # Get base recommendations for this error type
            base_recommendations = self._get_base_recommendations(category, code)
            
            # Customize recommendations based on error context
            customized_recommendations = self._customize_recommendations(
                base_recommendations, error_list
            )
            
            recommendations.extend(customized_recommendations)
        
        # Remove duplicates and prioritize
        recommendations = self._deduplicate_and_prioritize_recommendations(recommendations)
        
        return recommendations
    
    def assess_system_health(self, time_window_hours: int = 24) -> SystemHealthAssessment:
        """Perform comprehensive system health assessment."""
        cutoff_time = datetime.utcnow() - timedelta(hours=time_window_hours)
        recent_errors = [e for e in self.error_history if e.timestamp >= cutoff_time]
        
        # Analyze error patterns
        error_patterns = self.analyze_error_patterns(time_window_hours)
        
        # Calculate overall health score
        overall_health_score = self._calculate_overall_health_score(recent_errors)
        
        # Identify critical issues
        critical_issues = self._identify_critical_issues(recent_errors, error_patterns)
        
        # Identify warnings
        warnings = self._identify_warnings(recent_errors, error_patterns)
        
        # Generate recommendations
        recommendations = self.generate_troubleshooting_recommendations(recent_errors)
        
        # Calculate server health scores
        server_health_scores = self._calculate_server_health_scores(recent_errors)
        
        # Perform trend analysis
        trend_analysis = self._perform_trend_analysis(recent_errors)
        
        return SystemHealthAssessment(
            assessment_id=f"assessment_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            timestamp=datetime.utcnow(),
            overall_health_score=overall_health_score,
            critical_issues=critical_issues,
            warnings=warnings,
            recommendations=recommendations,
            error_patterns=error_patterns,
            server_health_scores=server_health_scores,
            trend_analysis=trend_analysis
        )
    
    def get_error_statistics(self, time_window_hours: int = 24) -> Dict[str, Any]:
        """Get comprehensive error statistics."""
        cutoff_time = datetime.utcnow() - timedelta(hours=time_window_hours)
        recent_errors = [e for e in self.error_history if e.timestamp >= cutoff_time]
        
        if not recent_errors:
            return {
                "total_errors": 0,
                "error_rate": 0.0,
                "most_common_errors": [],
                "server_error_distribution": {},
                "hourly_error_counts": [],
                "recovery_rate": 0.0
            }
        
        # Basic statistics
        total_errors = len(recent_errors)
        error_rate = total_errors / time_window_hours
        
        # Most common errors
        error_counter = Counter([e.error_code.value for e in recent_errors])
        most_common_errors = [
            {"error_code": code, "count": count, "percentage": (count / total_errors) * 100}
            for code, count in error_counter.most_common(10)
        ]
        
        # Server error distribution
        server_errors = defaultdict(int)
        for error in recent_errors:
            if error.context and error.context.server_name:
                server_errors[error.context.server_name] += 1
        
        # Hourly error counts
        hourly_counts = self._calculate_hourly_error_counts(recent_errors, time_window_hours)
        
        # Recovery rate
        recoverable_errors = sum(1 for e in recent_errors if e.is_recoverable)
        recovery_rate = recoverable_errors / total_errors if total_errors > 0 else 0.0
        
        return {
            "total_errors": total_errors,
            "error_rate": error_rate,
            "most_common_errors": most_common_errors,
            "server_error_distribution": dict(server_errors),
            "hourly_error_counts": hourly_counts,
            "recovery_rate": recovery_rate,
            "severity_distribution": self._calculate_severity_distribution(recent_errors),
            "category_distribution": self._calculate_category_distribution(recent_errors)
        }
    
    def _detect_frequency_patterns(self, errors: List[ErrorDetails]) -> List[ErrorPattern]:
        """Detect high-frequency error patterns."""
        patterns = []
        
        # Count errors by code and server
        error_counts = defaultdict(lambda: defaultdict(int))
        error_timestamps = defaultdict(lambda: defaultdict(list))
        
        for error in errors:
            server = error.context.server_name if error.context else "unknown"
            error_counts[error.error_code][server] += 1
            error_timestamps[error.error_code][server].append(error.timestamp)
        
        # Identify high-frequency patterns
        for error_code, server_counts in error_counts.items():
            total_count = sum(server_counts.values())
            
            if total_count >= 5:  # Threshold for high frequency
                servers_affected = list(server_counts.keys())
                all_timestamps = []
                for server_timestamps in error_timestamps[error_code].values():
                    all_timestamps.extend(server_timestamps)
                
                all_timestamps.sort()
                
                pattern = ErrorPattern(
                    pattern_id=f"freq_{error_code.value}_{len(patterns)}",
                    pattern_type="frequency",
                    description=f"High frequency of {error_code.value} errors ({total_count} occurrences)",
                    error_codes=[error_code],
                    servers_affected=servers_affected,
                    frequency=total_count,
                    first_occurrence=min(all_timestamps),
                    last_occurrence=max(all_timestamps),
                    severity_distribution=self._get_severity_distribution_for_errors(
                        [e for e in errors if e.error_code == error_code]
                    ),
                    confidence_score=min(1.0, total_count / 10.0)
                )
                
                # Add root cause hypothesis and recommendations
                pattern.root_cause_hypothesis = self._generate_frequency_hypothesis(error_code, total_count)
                pattern.recommended_actions = self._get_frequency_recommendations(error_code)
                
                patterns.append(pattern)
        
        return patterns
    
    def _detect_sequence_patterns(self, errors: List[ErrorDetails]) -> List[ErrorPattern]:
        """Detect error sequence patterns."""
        patterns = []
        
        # Sort errors by timestamp
        sorted_errors = sorted(errors, key=lambda e: e.timestamp)
        
        # Look for sequences of related errors
        sequence_window = timedelta(minutes=5)  # Errors within 5 minutes are considered a sequence
        
        i = 0
        while i < len(sorted_errors) - 1:
            sequence_errors = [sorted_errors[i]]
            j = i + 1
            
            while j < len(sorted_errors) and (sorted_errors[j].timestamp - sequence_errors[-1].timestamp) <= sequence_window:
                sequence_errors.append(sorted_errors[j])
                j += 1
            
            if len(sequence_errors) >= 3:  # Minimum sequence length
                error_codes = [e.error_code for e in sequence_errors]
                servers_affected = list(set([
                    e.context.server_name for e in sequence_errors 
                    if e.context and e.context.server_name
                ]))
                
                pattern = ErrorPattern(
                    pattern_id=f"seq_{i}_{len(patterns)}",
                    pattern_type="sequence",
                    description=f"Error sequence detected: {' -> '.join([c.value for c in error_codes[:3]])}{'...' if len(error_codes) > 3 else ''}",
                    error_codes=list(set(error_codes)),
                    servers_affected=servers_affected,
                    frequency=len(sequence_errors),
                    first_occurrence=sequence_errors[0].timestamp,
                    last_occurrence=sequence_errors[-1].timestamp,
                    severity_distribution=self._get_severity_distribution_for_errors(sequence_errors),
                    confidence_score=min(1.0, len(sequence_errors) / 5.0)
                )
                
                pattern.root_cause_hypothesis = self._generate_sequence_hypothesis(error_codes)
                pattern.recommended_actions = self._get_sequence_recommendations(error_codes)
                
                patterns.append(pattern)
            
            i = j if j > i + 1 else i + 1
        
        return patterns
    
    def _detect_correlation_patterns(self, errors: List[ErrorDetails]) -> List[ErrorPattern]:
        """Detect error correlation patterns."""
        patterns = []
        
        # Group errors by server and time windows
        time_window = timedelta(minutes=10)
        server_error_windows = defaultdict(list)
        
        for error in errors:
            server = error.context.server_name if error.context else "unknown"
            server_error_windows[server].append(error)
        
        # Look for correlated errors across servers
        for server, server_errors in server_error_windows.items():
            if len(server_errors) < 2:
                continue
            
            # Sort by timestamp
            server_errors.sort(key=lambda e: e.timestamp)
            
            # Find correlated error groups
            for i, error1 in enumerate(server_errors[:-1]):
                correlated_errors = [error1]
                
                for error2 in server_errors[i+1:]:
                    if (error2.timestamp - error1.timestamp) <= time_window:
                        if error2.category == error1.category or error2.error_code == error1.error_code:
                            correlated_errors.append(error2)
                    else:
                        break
                
                if len(correlated_errors) >= 2:
                    error_codes = list(set([e.error_code for e in correlated_errors]))
                    
                    pattern = ErrorPattern(
                        pattern_id=f"corr_{server}_{i}_{len(patterns)}",
                        pattern_type="correlation",
                        description=f"Correlated errors on {server}: {', '.join([c.value for c in error_codes])}",
                        error_codes=error_codes,
                        servers_affected=[server],
                        frequency=len(correlated_errors),
                        first_occurrence=correlated_errors[0].timestamp,
                        last_occurrence=correlated_errors[-1].timestamp,
                        severity_distribution=self._get_severity_distribution_for_errors(correlated_errors),
                        confidence_score=min(1.0, len(correlated_errors) / 3.0)
                    )
                    
                    pattern.root_cause_hypothesis = self._generate_correlation_hypothesis(server, error_codes)
                    pattern.recommended_actions = self._get_correlation_recommendations(server, error_codes)
                    
                    patterns.append(pattern)
        
        return patterns
    
    def _detect_temporal_patterns(self, errors: List[ErrorDetails]) -> List[ErrorPattern]:
        """Detect temporal error patterns."""
        patterns = []
        
        if len(errors) < 5:
            return patterns
        
        # Group errors by hour of day
        hourly_errors = defaultdict(list)
        for error in errors:
            hour = error.timestamp.hour
            hourly_errors[hour].append(error)
        
        # Find hours with significantly higher error rates
        error_counts_by_hour = {hour: len(errors) for hour, errors in hourly_errors.items()}
        if not error_counts_by_hour:
            return patterns
        
        mean_errors = statistics.mean(error_counts_by_hour.values())
        std_errors = statistics.stdev(error_counts_by_hour.values()) if len(error_counts_by_hour) > 1 else 0
        
        threshold = mean_errors + (2 * std_errors)  # 2 standard deviations above mean
        
        for hour, count in error_counts_by_hour.items():
            if count > threshold and count >= 3:
                hour_errors = hourly_errors[hour]
                error_codes = list(set([e.error_code for e in hour_errors]))
                servers_affected = list(set([
                    e.context.server_name for e in hour_errors 
                    if e.context and e.context.server_name
                ]))
                
                pattern = ErrorPattern(
                    pattern_id=f"temp_hour_{hour}_{len(patterns)}",
                    pattern_type="temporal",
                    description=f"High error rate during hour {hour}:00-{hour+1}:00 ({count} errors)",
                    error_codes=error_codes,
                    servers_affected=servers_affected,
                    frequency=count,
                    first_occurrence=min([e.timestamp for e in hour_errors]),
                    last_occurrence=max([e.timestamp for e in hour_errors]),
                    severity_distribution=self._get_severity_distribution_for_errors(hour_errors),
                    confidence_score=min(1.0, (count - mean_errors) / (std_errors or 1))
                )
                
                pattern.root_cause_hypothesis = self._generate_temporal_hypothesis(hour, count)
                pattern.recommended_actions = self._get_temporal_recommendations(hour)
                
                patterns.append(pattern)
        
        return patterns
    
    def _initialize_troubleshooting_rules(self):
        """Initialize troubleshooting rules for different error types."""
        # MCP Protocol errors
        self.troubleshooting_rules[f"{ErrorCategory.MCP_PROTOCOL.value}_{ErrorCode.MCP_CONNECTION_FAILED.value}"] = [
            TroubleshootingRecommendation(
                recommendation_id="mcp_conn_1",
                title="Check MCP Server Connectivity",
                description="Verify that the MCP server is running and accessible",
                priority="high",
                category="immediate",
                steps=[
                    "Check if MCP server process is running",
                    "Verify network connectivity to server endpoint",
                    "Test server response with curl or similar tool",
                    "Check firewall rules and port accessibility"
                ],
                expected_outcome="MCP server becomes accessible",
                estimated_time_minutes=10
            )
        ]
        
        # HTTP Request errors
        self.troubleshooting_rules[f"{ErrorCategory.HTTP_REQUEST.value}_{ErrorCode.HTTP_CONNECTION_ERROR.value}"] = [
            TroubleshootingRecommendation(
                recommendation_id="http_conn_1",
                title="Check HTTP Service Availability",
                description="Verify that the HTTP service is running and responding",
                priority="high",
                category="immediate",
                steps=[
                    "Check if HTTP service is running",
                    "Verify service health endpoint",
                    "Check service logs for errors",
                    "Restart service if necessary"
                ],
                expected_outcome="HTTP service becomes available",
                estimated_time_minutes=15,
                requires_restart=True
            )
        ]
        
        # Authentication errors
        self.troubleshooting_rules[f"{ErrorCategory.AUTHENTICATION.value}_{ErrorCode.AUTH_TOKEN_EXPIRED.value}"] = [
            TroubleshootingRecommendation(
                recommendation_id="auth_token_1",
                title="Refresh Authentication Token",
                description="Obtain a new authentication token",
                priority="medium",
                category="immediate",
                steps=[
                    "Check token expiration time",
                    "Refresh token using refresh endpoint",
                    "Update token in configuration",
                    "Verify new token works"
                ],
                expected_outcome="Authentication succeeds with new token",
                estimated_time_minutes=5
            )
        ]
    
    def _group_errors(self, errors: List[ErrorDetails]) -> Dict[Tuple[ErrorCategory, ErrorCode], List[ErrorDetails]]:
        """Group errors by category and code."""
        groups = defaultdict(list)
        for error in errors:
            key = (error.category, error.error_code)
            groups[key].append(error)
        return dict(groups)
    
    def _get_base_recommendations(self, category: ErrorCategory, code: ErrorCode) -> List[TroubleshootingRecommendation]:
        """Get base recommendations for error category and code."""
        key = f"{category.value}_{code.value}"
        return self.troubleshooting_rules.get(key, [])
    
    def _customize_recommendations(self, base_recommendations: List[TroubleshootingRecommendation],
                                 errors: List[ErrorDetails]) -> List[TroubleshootingRecommendation]:
        """Customize recommendations based on error context."""
        # For now, return base recommendations
        # In the future, this could customize based on error frequency, affected servers, etc.
        return base_recommendations
    
    def _deduplicate_and_prioritize_recommendations(self, recommendations: List[TroubleshootingRecommendation]) -> List[TroubleshootingRecommendation]:
        """Remove duplicates and prioritize recommendations."""
        seen_ids = set()
        unique_recommendations = []
        
        for rec in recommendations:
            if rec.recommendation_id not in seen_ids:
                seen_ids.add(rec.recommendation_id)
                unique_recommendations.append(rec)
        
        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        unique_recommendations.sort(key=lambda r: priority_order.get(r.priority, 3))
        
        return unique_recommendations
    
    def _calculate_overall_health_score(self, errors: List[ErrorDetails]) -> float:
        """Calculate overall system health score."""
        if not errors:
            return 1.0
        
        # Base score starts at 1.0 and decreases based on errors
        base_score = 1.0
        
        # Weight errors by severity
        severity_weights = {
            ErrorSeverity.CRITICAL: 0.3,
            ErrorSeverity.ERROR: 0.1,
            ErrorSeverity.WARNING: 0.05,
            ErrorSeverity.INFO: 0.01
        }
        
        total_weight = 0
        for error in errors:
            weight = severity_weights.get(error.severity, 0.1)
            total_weight += weight
        
        # Normalize by time window (assume 24 hours)
        normalized_weight = min(total_weight / 24.0, 1.0)
        
        return max(0.0, base_score - normalized_weight)
    
    def _identify_critical_issues(self, errors: List[ErrorDetails], patterns: List[ErrorPattern]) -> List[str]:
        """Identify critical issues from errors and patterns."""
        issues = []
        
        # Critical errors
        critical_errors = [e for e in errors if e.severity == ErrorSeverity.CRITICAL]
        if critical_errors:
            issues.append(f"{len(critical_errors)} critical errors detected")
        
        # High-frequency patterns
        high_freq_patterns = [p for p in patterns if p.frequency >= 10]
        if high_freq_patterns:
            issues.append(f"{len(high_freq_patterns)} high-frequency error patterns detected")
        
        # Multiple server failures
        failed_servers = set()
        for error in errors:
            if error.context and error.context.server_name:
                failed_servers.add(error.context.server_name)
        
        if len(failed_servers) >= 3:
            issues.append(f"Multiple servers affected: {', '.join(list(failed_servers)[:3])}{'...' if len(failed_servers) > 3 else ''}")
        
        return issues
    
    def _identify_warnings(self, errors: List[ErrorDetails], patterns: List[ErrorPattern]) -> List[str]:
        """Identify warnings from errors and patterns."""
        warnings = []
        
        # Warning-level errors
        warning_errors = [e for e in errors if e.severity == ErrorSeverity.WARNING]
        if len(warning_errors) >= 5:
            warnings.append(f"{len(warning_errors)} warning-level errors detected")
        
        # Authentication issues
        auth_errors = [e for e in errors if e.category == ErrorCategory.AUTHENTICATION]
        if auth_errors:
            warnings.append(f"{len(auth_errors)} authentication errors detected")
        
        # Network issues
        network_errors = [e for e in errors if e.category == ErrorCategory.NETWORK]
        if len(network_errors) >= 3:
            warnings.append(f"{len(network_errors)} network errors detected")
        
        return warnings
    
    def _calculate_server_health_scores(self, errors: List[ErrorDetails]) -> Dict[str, float]:
        """Calculate health scores for individual servers."""
        server_errors = defaultdict(list)
        
        for error in errors:
            if error.context and error.context.server_name:
                server_errors[error.context.server_name].append(error)
        
        server_scores = {}
        for server, server_error_list in server_errors.items():
            # Calculate score based on error count and severity
            score = 1.0
            for error in server_error_list:
                if error.severity == ErrorSeverity.CRITICAL:
                    score -= 0.2
                elif error.severity == ErrorSeverity.ERROR:
                    score -= 0.1
                elif error.severity == ErrorSeverity.WARNING:
                    score -= 0.05
            
            server_scores[server] = max(0.0, score)
        
        return server_scores
    
    def _perform_trend_analysis(self, errors: List[ErrorDetails]) -> Dict[str, Any]:
        """Perform trend analysis on errors."""
        if len(errors) < 2:
            return {"trend": "insufficient_data"}
        
        # Sort errors by timestamp
        sorted_errors = sorted(errors, key=lambda e: e.timestamp)
        
        # Calculate error rate over time
        time_buckets = defaultdict(int)
        for error in sorted_errors:
            # Group by hour
            hour_key = error.timestamp.replace(minute=0, second=0, microsecond=0)
            time_buckets[hour_key] += 1
        
        if len(time_buckets) < 2:
            return {"trend": "insufficient_time_data"}
        
        # Calculate trend
        sorted_times = sorted(time_buckets.keys())
        error_counts = [time_buckets[t] for t in sorted_times]
        
        # Simple linear trend calculation
        n = len(error_counts)
        x_values = list(range(n))
        
        # Calculate slope
        x_mean = sum(x_values) / n
        y_mean = sum(error_counts) / n
        
        numerator = sum((x_values[i] - x_mean) * (error_counts[i] - y_mean) for i in range(n))
        denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            slope = 0
        else:
            slope = numerator / denominator
        
        trend_direction = "increasing" if slope > 0.1 else "decreasing" if slope < -0.1 else "stable"
        
        return {
            "trend": trend_direction,
            "slope": slope,
            "recent_error_rate": error_counts[-1] if error_counts else 0,
            "average_error_rate": y_mean,
            "time_periods_analyzed": len(time_buckets)
        }
    
    def _calculate_hourly_error_counts(self, errors: List[ErrorDetails], time_window_hours: int) -> List[Dict[str, Any]]:
        """Calculate hourly error counts."""
        hourly_counts = []
        
        # Create hourly buckets
        end_time = datetime.utcnow()
        for i in range(time_window_hours):
            hour_start = end_time - timedelta(hours=i+1)
            hour_end = end_time - timedelta(hours=i)
            
            hour_errors = [
                e for e in errors 
                if hour_start <= e.timestamp < hour_end
            ]
            
            hourly_counts.append({
                "hour": hour_start.strftime("%Y-%m-%d %H:00"),
                "error_count": len(hour_errors),
                "critical_count": len([e for e in hour_errors if e.severity == ErrorSeverity.CRITICAL]),
                "error_count": len([e for e in hour_errors if e.severity == ErrorSeverity.ERROR]),
                "warning_count": len([e for e in hour_errors if e.severity == ErrorSeverity.WARNING])
            })
        
        return list(reversed(hourly_counts))
    
    def _calculate_severity_distribution(self, errors: List[ErrorDetails]) -> Dict[str, int]:
        """Calculate distribution of errors by severity."""
        distribution = defaultdict(int)
        for error in errors:
            distribution[error.severity.value] += 1
        return dict(distribution)
    
    def _calculate_category_distribution(self, errors: List[ErrorDetails]) -> Dict[str, int]:
        """Calculate distribution of errors by category."""
        distribution = defaultdict(int)
        for error in errors:
            distribution[error.category.value] += 1
        return dict(distribution)
    
    def _get_severity_distribution_for_errors(self, errors: List[ErrorDetails]) -> Dict[str, int]:
        """Get severity distribution for specific error list."""
        return self._calculate_severity_distribution(errors)
    
    def _generate_frequency_hypothesis(self, error_code: ErrorCode, count: int) -> str:
        """Generate hypothesis for high-frequency errors."""
        if count >= 20:
            return f"Possible system overload or configuration issue causing repeated {error_code.value} errors"
        elif count >= 10:
            return f"Intermittent issue causing frequent {error_code.value} errors"
        else:
            return f"Recurring {error_code.value} error pattern detected"
    
    def _generate_sequence_hypothesis(self, error_codes: List[ErrorCode]) -> str:
        """Generate hypothesis for error sequences."""
        return f"Cascading failure pattern: {' -> '.join([c.value for c in error_codes[:3]])}"
    
    def _generate_correlation_hypothesis(self, server: str, error_codes: List[ErrorCode]) -> str:
        """Generate hypothesis for correlated errors."""
        return f"Server {server} experiencing correlated issues: {', '.join([c.value for c in error_codes])}"
    
    def _generate_temporal_hypothesis(self, hour: int, count: int) -> str:
        """Generate hypothesis for temporal patterns."""
        return f"Peak error activity during hour {hour}:00-{hour+1}:00 suggests scheduled process or load pattern"
    
    def _get_frequency_recommendations(self, error_code: ErrorCode) -> List[str]:
        """Get recommendations for high-frequency errors."""
        return [
            f"Investigate root cause of {error_code.value} errors",
            "Check system resources and performance",
            "Review recent configuration changes",
            "Consider implementing circuit breaker"
        ]
    
    def _get_sequence_recommendations(self, error_codes: List[ErrorCode]) -> List[str]:
        """Get recommendations for error sequences."""
        return [
            "Investigate cascading failure pattern",
            "Check dependencies between components",
            "Review error handling and recovery mechanisms",
            "Consider implementing better isolation"
        ]
    
    def _get_correlation_recommendations(self, server: str, error_codes: List[ErrorCode]) -> List[str]:
        """Get recommendations for correlated errors."""
        return [
            f"Focus troubleshooting efforts on server {server}",
            "Check server-specific configuration and resources",
            "Review server logs for additional context",
            "Consider server restart if issues persist"
        ]
    
    def _get_temporal_recommendations(self, hour: int) -> List[str]:
        """Get recommendations for temporal patterns."""
        return [
            f"Investigate scheduled processes running during hour {hour}:00",
            "Check system load and resource usage patterns",
            "Consider load balancing or resource scaling",
            "Review cron jobs and scheduled tasks"
        ]
    
    def _clear_analysis_cache(self):
        """Clear analysis cache when new errors are added."""
        self.analysis_cache.clear()
        # Keep pattern cache but mark as potentially stale
        for pattern in self.pattern_cache.values():
            pattern.confidence_score *= 0.9  # Reduce confidence over time