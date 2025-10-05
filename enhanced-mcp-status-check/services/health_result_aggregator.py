"""
Health Result Aggregator

This module implements the Health Result Aggregator for combining dual health check results
from both MCP tools/list requests and REST API health checks with intelligent aggregation logic.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from statistics import mean

from models.dual_health_models import (
    MCPHealthCheckResult,
    RESTHealthCheckResult,
    DualHealthCheckResult,
    CombinedHealthMetrics,
    AggregationConfig,
    PriorityConfig,
    ServerStatus,
    EnhancedServerConfig
)


logger = logging.getLogger(__name__)


class HealthResultAggregator:
    """
    Health Result Aggregator for combining dual monitoring results.
    
    This class provides intelligent result combination logic with priority weighting,
    status determination, and combined metrics calculation from MCP and REST results.
    """
    
    def __init__(self, default_config: Optional[AggregationConfig] = None):
        """
        Initialize Health Result Aggregator.
        
        Args:
            default_config: Default aggregation configuration
        """
        self.default_config = default_config or self._create_default_config()
        
    def _create_default_config(self) -> AggregationConfig:
        """Create default aggregation configuration."""
        priority_config = PriorityConfig(
            mcp_priority_weight=0.6,
            rest_priority_weight=0.4,
            require_both_success_for_healthy=False,
            degraded_on_single_failure=True
        )
        
        return AggregationConfig(
            priority_config=priority_config,
            health_score_calculation="weighted_average",
            failure_threshold=0.5,
            degraded_threshold=0.7
        )
    
    def determine_overall_status(
        self,
        mcp_success: bool,
        rest_success: bool,
        priority_config: PriorityConfig
    ) -> ServerStatus:
        """
        Determine overall server status based on dual health check results.
        
        Args:
            mcp_success: MCP health check success status
            rest_success: REST health check success status
            priority_config: Priority configuration for decision making
            
        Returns:
            ServerStatus: Overall server status
        """
        # Both successful
        if mcp_success and rest_success:
            return ServerStatus.HEALTHY
        
        # Both failed
        if not mcp_success and not rest_success:
            return ServerStatus.UNHEALTHY
        
        # Mixed results - apply priority logic
        if priority_config.require_both_success_for_healthy:
            # Strict mode: require both to be healthy
            return ServerStatus.DEGRADED
        
        if priority_config.degraded_on_single_failure:
            # Conservative mode: single failure means degraded
            return ServerStatus.DEGRADED
        
        # Permissive mode: success of higher priority path determines status
        if mcp_success and priority_config.mcp_priority_weight > priority_config.rest_priority_weight:
            return ServerStatus.HEALTHY
        elif rest_success and priority_config.rest_priority_weight > priority_config.mcp_priority_weight:
            return ServerStatus.HEALTHY
        else:
            return ServerStatus.DEGRADED
    
    def calculate_health_score(
        self,
        mcp_result: Optional[MCPHealthCheckResult],
        rest_result: Optional[RESTHealthCheckResult],
        aggregation_config: AggregationConfig
    ) -> float:
        """
        Calculate combined health score from dual results.
        
        Args:
            mcp_result: MCP health check result
            rest_result: REST health check result
            aggregation_config: Aggregation configuration
            
        Returns:
            float: Health score between 0.0 and 1.0
        """
        mcp_score = self._calculate_mcp_score(mcp_result) if mcp_result else 0.0
        rest_score = self._calculate_rest_score(rest_result) if rest_result else 0.0
        
        # Handle cases where one or both results are missing
        if mcp_result is None and rest_result is None:
            return 0.0
        elif mcp_result is None:
            return rest_score
        elif rest_result is None:
            return mcp_score
        
        # Calculate combined score based on method
        method = aggregation_config.health_score_calculation
        priority_config = aggregation_config.priority_config
        
        if method == "weighted_average":
            return (
                mcp_score * priority_config.mcp_priority_weight +
                rest_score * priority_config.rest_priority_weight
            )
        elif method == "minimum":
            return min(mcp_score, rest_score)
        elif method == "maximum":
            return max(mcp_score, rest_score)
        else:
            # Default to weighted average
            logger.warning(f"Unknown health score calculation method: {method}, using weighted_average")
            return (
                mcp_score * priority_config.mcp_priority_weight +
                rest_score * priority_config.rest_priority_weight
            )
    
    def _calculate_mcp_score(self, mcp_result: MCPHealthCheckResult) -> float:
        """
        Calculate health score from MCP result.
        
        Args:
            mcp_result: MCP health check result
            
        Returns:
            float: MCP health score between 0.0 and 1.0
        """
        if not mcp_result.success:
            return 0.0
        
        score = 1.0
        
        # Penalize for missing expected tools
        if mcp_result.validation_result:
            validation = mcp_result.validation_result
            if validation.expected_tools_found and validation.missing_tools:
                expected_count = len(validation.expected_tools_found) + len(validation.missing_tools)
                found_count = len(validation.expected_tools_found)
                tool_score = found_count / expected_count if expected_count > 0 else 1.0
                score *= tool_score
            
            # Penalize for validation errors
            if validation.validation_errors:
                error_penalty = min(0.5, len(validation.validation_errors) * 0.1)
                score *= (1.0 - error_penalty)
        
        # Penalize for slow response times (>5 seconds)
        if mcp_result.response_time_ms > 5000:
            time_penalty = min(0.3, (mcp_result.response_time_ms - 5000) / 10000)
            score *= (1.0 - time_penalty)
        
        return max(0.0, min(1.0, score))
    
    def _calculate_rest_score(self, rest_result: RESTHealthCheckResult) -> float:
        """
        Calculate health score from REST result.
        
        Args:
            rest_result: REST health check result
            
        Returns:
            float: REST health score between 0.0 and 1.0
        """
        if not rest_result.success:
            return 0.0
        
        score = 1.0
        
        # Penalize for non-2xx status codes
        if rest_result.status_code and not (200 <= rest_result.status_code < 300):
            if 300 <= rest_result.status_code < 400:
                score *= 0.8  # Redirect penalty
            elif 400 <= rest_result.status_code < 500:
                score *= 0.3  # Client error penalty
            else:
                score *= 0.1  # Server error penalty
        
        # Penalize for validation errors
        if rest_result.validation_result and rest_result.validation_result.validation_errors:
            error_count = len(rest_result.validation_result.validation_errors)
            error_penalty = min(0.5, error_count * 0.1)
            score *= (1.0 - error_penalty)
        
        # Penalize for slow response times (>3 seconds)
        if rest_result.response_time_ms > 3000:
            time_penalty = min(0.3, (rest_result.response_time_ms - 3000) / 7000)
            score *= (1.0 - time_penalty)
        
        return max(0.0, min(1.0, score))
    
    def create_combined_metrics(
        self,
        mcp_result: Optional[MCPHealthCheckResult],
        rest_result: Optional[RESTHealthCheckResult]
    ) -> CombinedHealthMetrics:
        """
        Create combined health metrics from MCP and REST results.
        
        Args:
            mcp_result: MCP health check result
            rest_result: REST health check result
            
        Returns:
            CombinedHealthMetrics: Combined metrics
        """
        # Response time metrics
        mcp_response_time = mcp_result.response_time_ms if mcp_result else 0.0
        rest_response_time = rest_result.response_time_ms if rest_result else 0.0
        
        # Calculate combined response time
        if mcp_result and rest_result:
            combined_response_time = mean([mcp_response_time, rest_response_time])
        elif mcp_result:
            combined_response_time = mcp_response_time
        elif rest_result:
            combined_response_time = rest_response_time
        else:
            combined_response_time = 0.0
        
        # Success rate metrics (simplified for single check)
        mcp_success_rate = 1.0 if mcp_result and mcp_result.success else 0.0
        rest_success_rate = 1.0 if rest_result and rest_result.success else 0.0
        
        # Calculate combined success rate
        if mcp_result and rest_result:
            combined_success_rate = mean([mcp_success_rate, rest_success_rate])
        elif mcp_result:
            combined_success_rate = mcp_success_rate
        elif rest_result:
            combined_success_rate = rest_success_rate
        else:
            combined_success_rate = 0.0
        
        # Tool-specific metrics
        tools_available_count = 0
        tools_expected_count = 0
        tools_availability_percentage = 0.0
        
        if mcp_result and mcp_result.validation_result:
            validation = mcp_result.validation_result
            tools_available_count = len(validation.expected_tools_found)
            tools_expected_count = tools_available_count + len(validation.missing_tools)
            if tools_expected_count > 0:
                tools_availability_percentage = (tools_available_count / tools_expected_count) * 100
        
        # HTTP-specific metrics
        http_status_codes = {}
        health_endpoint_availability = 0.0
        
        if rest_result and rest_result.status_code:
            http_status_codes[rest_result.status_code] = 1
            health_endpoint_availability = 1.0 if rest_result.success else 0.0
        
        return CombinedHealthMetrics(
            mcp_response_time_ms=mcp_response_time,
            rest_response_time_ms=rest_response_time,
            combined_response_time_ms=combined_response_time,
            mcp_success_rate=mcp_success_rate,
            rest_success_rate=rest_success_rate,
            combined_success_rate=combined_success_rate,
            tools_available_count=tools_available_count,
            tools_expected_count=tools_expected_count,
            tools_availability_percentage=tools_availability_percentage,
            http_status_codes=http_status_codes,
            health_endpoint_availability=health_endpoint_availability
        )
    
    def determine_available_paths(
        self,
        mcp_result: Optional[MCPHealthCheckResult],
        rest_result: Optional[RESTHealthCheckResult]
    ) -> List[str]:
        """
        Determine available monitoring paths based on results.
        
        Args:
            mcp_result: MCP health check result
            rest_result: REST health check result
            
        Returns:
            List[str]: Available paths (combinations of "mcp", "rest")
        """
        available_paths = []
        
        if mcp_result and mcp_result.success:
            available_paths.append("mcp")
        
        if rest_result and rest_result.success:
            available_paths.append("rest")
        
        # Determine combined availability
        if "mcp" in available_paths and "rest" in available_paths:
            available_paths.append("both")
        elif not available_paths:
            available_paths.append("none")
        
        return available_paths
    
    def aggregate_dual_results(
        self,
        mcp_result: Optional[MCPHealthCheckResult],
        rest_result: Optional[RESTHealthCheckResult],
        aggregation_config: Optional[AggregationConfig] = None
    ) -> DualHealthCheckResult:
        """
        Aggregate dual health check results into combined result.
        
        Args:
            mcp_result: MCP health check result
            rest_result: REST health check result
            aggregation_config: Optional aggregation configuration
            
        Returns:
            DualHealthCheckResult: Combined dual health check result
        """
        config = aggregation_config or self.default_config
        
        # Validate configuration
        config_errors = config.validate()
        if config_errors:
            logger.warning(f"Invalid aggregation config: {config_errors}")
            config = self.default_config
        
        # Determine server name and timestamp
        server_name = ""
        timestamp = datetime.now()
        
        if mcp_result:
            server_name = mcp_result.server_name
            timestamp = mcp_result.timestamp
        elif rest_result:
            server_name = rest_result.server_name
            timestamp = rest_result.timestamp
        
        # Extract success status
        mcp_success = mcp_result.success if mcp_result else False
        rest_success = rest_result.success if rest_result else False
        
        # Determine overall status
        overall_status = self.determine_overall_status(
            mcp_success=mcp_success,
            rest_success=rest_success,
            priority_config=config.priority_config
        )
        
        # Calculate health score
        health_score = self.calculate_health_score(
            mcp_result=mcp_result,
            rest_result=rest_result,
            aggregation_config=config
        )
        
        # Create combined metrics
        combined_metrics = self.create_combined_metrics(
            mcp_result=mcp_result,
            rest_result=rest_result
        )
        
        # Determine available paths
        available_paths = self.determine_available_paths(
            mcp_result=mcp_result,
            rest_result=rest_result
        )
        
        # Extract error messages
        mcp_error_message = None
        if mcp_result and not mcp_result.success:
            if mcp_result.connection_error:
                mcp_error_message = mcp_result.connection_error
            elif mcp_result.mcp_error:
                mcp_error_message = str(mcp_result.mcp_error)
            elif mcp_result.validation_result and mcp_result.validation_result.validation_errors:
                mcp_error_message = "; ".join(mcp_result.validation_result.validation_errors)
        
        rest_error_message = None
        if rest_result and not rest_result.success:
            if rest_result.connection_error:
                rest_error_message = rest_result.connection_error
            elif rest_result.http_error:
                rest_error_message = rest_result.http_error
            elif rest_result.validation_result and rest_result.validation_result.validation_errors:
                rest_error_message = "; ".join(rest_result.validation_result.validation_errors)
        
        # Determine overall success
        overall_success = overall_status == ServerStatus.HEALTHY
        
        # Create dual health check result
        dual_result = DualHealthCheckResult(
            server_name=server_name,
            timestamp=timestamp,
            overall_status=overall_status,
            overall_success=overall_success,
            mcp_result=mcp_result,
            mcp_success=mcp_success,
            mcp_response_time_ms=mcp_result.response_time_ms if mcp_result else 0.0,
            mcp_tools_count=mcp_result.tools_count if mcp_result else None,
            mcp_error_message=mcp_error_message,
            rest_result=rest_result,
            rest_success=rest_success,
            rest_response_time_ms=rest_result.response_time_ms if rest_result else 0.0,
            rest_status_code=rest_result.status_code if rest_result else None,
            rest_error_message=rest_error_message,
            combined_response_time_ms=combined_metrics.combined_response_time_ms,
            health_score=health_score,
            available_paths=available_paths,
            combined_metrics=combined_metrics
        )
        
        logger.info(f"Aggregated dual health check for {server_name}: "
                   f"status={overall_status.value}, score={health_score:.3f}, "
                   f"paths={available_paths}")
        
        return dual_result
    
    def aggregate_multiple_dual_results(
        self,
        dual_results: List[tuple[Optional[MCPHealthCheckResult], Optional[RESTHealthCheckResult]]],
        aggregation_config: Optional[AggregationConfig] = None
    ) -> List[DualHealthCheckResult]:
        """
        Aggregate multiple dual health check result pairs.
        
        Args:
            dual_results: List of (MCP result, REST result) tuples
            aggregation_config: Optional aggregation configuration
            
        Returns:
            List[DualHealthCheckResult]: List of aggregated results
        """
        config = aggregation_config or self.default_config
        
        aggregated_results = []
        for mcp_result, rest_result in dual_results:
            try:
                dual_result = self.aggregate_dual_results(
                    mcp_result=mcp_result,
                    rest_result=rest_result,
                    aggregation_config=config
                )
                aggregated_results.append(dual_result)
            except Exception as e:
                logger.error(f"Failed to aggregate dual result: {e}")
                # Create error result
                server_name = ""
                if mcp_result:
                    server_name = mcp_result.server_name
                elif rest_result:
                    server_name = rest_result.server_name
                
                error_result = DualHealthCheckResult(
                    server_name=server_name,
                    timestamp=datetime.now(),
                    overall_status=ServerStatus.UNKNOWN,
                    overall_success=False,
                    mcp_result=mcp_result,
                    rest_result=rest_result,
                    mcp_error_message=f"Aggregation error: {str(e)}",
                    available_paths=["none"]
                )
                aggregated_results.append(error_result)
        
        return aggregated_results
    
    def create_aggregation_summary(
        self,
        dual_results: List[DualHealthCheckResult]
    ) -> Dict[str, Any]:
        """
        Create summary statistics from aggregated dual results.
        
        Args:
            dual_results: List of dual health check results
            
        Returns:
            Dict[str, Any]: Summary statistics
        """
        if not dual_results:
            return {
                "total_servers": 0,
                "healthy_servers": 0,
                "degraded_servers": 0,
                "unhealthy_servers": 0,
                "unknown_servers": 0,
                "average_health_score": 0.0,
                "average_response_time_ms": 0.0,
                "mcp_success_rate": 0.0,
                "rest_success_rate": 0.0,
                "combined_success_rate": 0.0
            }
        
        # Count servers by status
        status_counts = {
            ServerStatus.HEALTHY: 0,
            ServerStatus.DEGRADED: 0,
            ServerStatus.UNHEALTHY: 0,
            ServerStatus.UNKNOWN: 0
        }
        
        for result in dual_results:
            status_counts[result.overall_status] += 1
        
        # Calculate averages
        health_scores = [r.health_score for r in dual_results]
        response_times = [r.combined_response_time_ms for r in dual_results]
        mcp_successes = [r.mcp_success for r in dual_results]
        rest_successes = [r.rest_success for r in dual_results]
        combined_successes = [r.overall_success for r in dual_results]
        
        return {
            "total_servers": len(dual_results),
            "healthy_servers": status_counts[ServerStatus.HEALTHY],
            "degraded_servers": status_counts[ServerStatus.DEGRADED],
            "unhealthy_servers": status_counts[ServerStatus.UNHEALTHY],
            "unknown_servers": status_counts[ServerStatus.UNKNOWN],
            "average_health_score": mean(health_scores) if health_scores else 0.0,
            "average_response_time_ms": mean(response_times) if response_times else 0.0,
            "mcp_success_rate": sum(mcp_successes) / len(mcp_successes) if mcp_successes else 0.0,
            "rest_success_rate": sum(rest_successes) / len(rest_successes) if rest_successes else 0.0,
            "combined_success_rate": sum(combined_successes) / len(combined_successes) if combined_successes else 0.0
        }
    
    def validate_aggregation_rules(
        self,
        aggregation_config: AggregationConfig
    ) -> List[str]:
        """
        Validate aggregation rules and configuration.
        
        Args:
            aggregation_config: Aggregation configuration to validate
            
        Returns:
            List[str]: List of validation errors
        """
        return aggregation_config.validate()
    
    def update_default_config(
        self,
        new_config: AggregationConfig
    ) -> bool:
        """
        Update default aggregation configuration.
        
        Args:
            new_config: New aggregation configuration
            
        Returns:
            bool: True if update successful, False if validation failed
        """
        validation_errors = self.validate_aggregation_rules(new_config)
        if validation_errors:
            logger.error(f"Cannot update default config due to validation errors: {validation_errors}")
            return False
        
        self.default_config = new_config
        logger.info("Default aggregation configuration updated successfully")
        return True