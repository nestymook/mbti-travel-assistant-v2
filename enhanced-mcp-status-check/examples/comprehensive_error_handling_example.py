"""
Comprehensive example demonstrating error handling and logging system.

This example shows how to use the enhanced error handling and logging
system for dual monitoring operations with comprehensive error analysis.
"""

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path

from ..models.error_models import (
    ErrorCode, ErrorContext, ErrorSeverity, ErrorCategory
)
from ..models.logging_models import (
    LogLevel, LogCategory, OperationType, LogContext, PerformanceMetrics
)
from ..services.error_handler import ErrorHandler
from ..services.structured_logger import StructuredLogger, configure_logging
from ..services.error_analyzer import ErrorAnalyzer


class DualMonitoringSimulator:
    """Simulator for dual monitoring operations with error handling."""
    
    def __init__(self):
        """Initialize the simulator."""
        # Configure logging
        self.logger = configure_logging(
            log_level=LogLevel.INFO,
            file_path="logs/dual_monitoring.log",
            console_output=True,
            json_format=True
        )
        
        # Initialize error handling and analysis
        self.error_handler = ErrorHandler()
        self.analyzer = ErrorAnalyzer()
        
        # Register error callbacks
        self._register_error_callbacks()
    
    def _register_error_callbacks(self):
        """Register callbacks for specific error types."""
        def on_mcp_connection_failed(error):
            self.logger.warning(
                f"MCP connection failed for {error.context.server_name}",
                LogCategory.MCP_PROTOCOL,
                tags=["connection_failure", "mcp"]
            )
        
        def on_auth_token_expired(error):
            self.logger.info(
                f"Token expired for {error.context.server_name}, will refresh",
                LogCategory.AUTHENTICATION,
                tags=["token_refresh", "auth"]
            )
        
        self.error_handler.register_error_callback(
            ErrorCode.MCP_CONNECTION_FAILED, on_mcp_connection_failed
        )
        self.error_handler.register_error_callback(
            ErrorCode.AUTH_TOKEN_EXPIRED, on_auth_token_expired
        )
    
    async def simulate_mcp_health_check(self, server_name: str, should_fail: bool = False):
        """Simulate MCP health check with potential failures."""
        context = LogContext(
            server_name=server_name,
            operation_type=OperationType.MCP_TOOLS_LIST,
            request_id=f"mcp_req_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        )
        
        # Start performance tracking
        with self.logger.push_context(context):
            metrics = self.logger.start_performance_tracking("mcp_health_check")
            
            try:
                self.logger.info(f"Starting MCP health check for {server_name}")
                
                if should_fail:
                    # Simulate different types of failures
                    import random
                    failure_type = random.choice([
                        "connection", "jsonrpc", "tools_missing", "timeout"
                    ])
                    
                    if failure_type == "connection":
                        raise ConnectionError("Connection refused")
                    elif failure_type == "jsonrpc":
                        raise ValueError("Invalid JSON-RPC response")
                    elif failure_type == "tools_missing":
                        raise Exception("Expected tools not found")
                    else:
                        raise TimeoutError("Request timeout")
                
                # Simulate successful check
                await asyncio.sleep(0.1)  # Simulate network delay
                
                self.logger.log_mcp_protocol(
                    method="tools/list",
                    request_id=context.request_id,
                    success=True,
                    tools_count=5
                )
                
                return {
                    "success": True,
                    "tools_count": 5,
                    "response_time_ms": 100
                }
                
            except Exception as e:
                # Handle the error
                error_context = ErrorContext(
                    server_name=server_name,
                    endpoint_url=f"http://{server_name}:8080/mcp",
                    request_id=context.request_id,
                    operation="mcp_health_check"
                )
                
                error = self.error_handler.handle_mcp_protocol_error(
                    e, error_context, {"method": "tools/list", "id": context.request_id}
                )
                
                # Log the error
                self.logger.log_error(error)
                
                # Add to analyzer
                self.analyzer.add_error(error)
                
                return {
                    "success": False,
                    "error": error.message,
                    "error_code": error.error_code.value
                }
                
            finally:
                # End performance tracking
                completed_metrics = self.logger.end_performance_tracking()
                
                self.logger.log_health_check(
                    server_name=server_name,
                    check_type="mcp",
                    success=not should_fail,
                    response_time_ms=completed_metrics.duration_ms if completed_metrics else 0
                )
    
    async def simulate_rest_health_check(self, server_name: str, should_fail: bool = False):
        """Simulate REST health check with potential failures."""
        context = LogContext(
            server_name=server_name,
            operation_type=OperationType.REST_HEALTH_CHECK,
            request_id=f"rest_req_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        )
        
        with self.logger.push_context(context):
            metrics = self.logger.start_performance_tracking("rest_health_check")
            
            try:
                self.logger.info(f"Starting REST health check for {server_name}")
                
                if should_fail:
                    # Simulate different HTTP failures
                    import random
                    failure_type = random.choice([
                        "connection", "timeout", "auth", "server_error"
                    ])
                    
                    if failure_type == "connection":
                        raise ConnectionError("Connection refused")
                    elif failure_type == "timeout":
                        raise TimeoutError("Request timeout")
                    elif failure_type == "auth":
                        raise Exception("Authentication failed")
                    else:
                        raise Exception("Internal server error")
                
                # Simulate successful check
                await asyncio.sleep(0.05)  # Simulate network delay
                
                self.logger.log_http_request(
                    method="GET",
                    url=f"http://{server_name}:8080/status/health",
                    status_code=200,
                    response_size_bytes=256,
                    success=True
                )
                
                return {
                    "success": True,
                    "status_code": 200,
                    "response_time_ms": 50
                }
                
            except Exception as e:
                # Handle the error
                error_context = ErrorContext(
                    server_name=server_name,
                    endpoint_url=f"http://{server_name}:8080/status/health",
                    request_id=context.request_id,
                    operation="rest_health_check"
                )
                
                # Determine status code based on error type
                status_code = None
                if "timeout" in str(e).lower():
                    status_code = None  # No response
                elif "auth" in str(e).lower():
                    status_code = 401
                elif "server error" in str(e).lower():
                    status_code = 500
                
                error = self.error_handler.handle_http_request_error(
                    e, error_context, status_code=status_code
                )
                
                # Log the error
                self.logger.log_error(error)
                
                # Add to analyzer
                self.analyzer.add_error(error)
                
                return {
                    "success": False,
                    "error": error.message,
                    "error_code": error.error_code.value,
                    "status_code": status_code
                }
                
            finally:
                # End performance tracking
                completed_metrics = self.logger.end_performance_tracking()
                
                self.logger.log_health_check(
                    server_name=server_name,
                    check_type="rest",
                    success=not should_fail,
                    response_time_ms=completed_metrics.duration_ms if completed_metrics else 0
                )
    
    async def simulate_dual_health_check(self, server_name: str, 
                                       mcp_should_fail: bool = False,
                                       rest_should_fail: bool = False):
        """Simulate dual health check combining MCP and REST checks."""
        context = LogContext(
            server_name=server_name,
            operation_type=OperationType.DUAL_HEALTH_CHECK,
            request_id=f"dual_req_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        )
        
        with self.logger.push_context(context):
            self.logger.info(f"Starting dual health check for {server_name}")
            
            # Perform both checks concurrently
            mcp_task = asyncio.create_task(
                self.simulate_mcp_health_check(server_name, mcp_should_fail)
            )
            rest_task = asyncio.create_task(
                self.simulate_rest_health_check(server_name, rest_should_fail)
            )
            
            mcp_result, rest_result = await asyncio.gather(mcp_task, rest_task)
            
            # Determine overall status
            overall_success = mcp_result["success"] and rest_result["success"]
            
            if overall_success:
                status = "HEALTHY"
            elif mcp_result["success"] or rest_result["success"]:
                status = "DEGRADED"
            else:
                status = "UNHEALTHY"
            
            self.logger.info(
                f"Dual health check completed for {server_name}: {status}",
                tags=["dual_check", "aggregation"]
            )
            
            return {
                "server_name": server_name,
                "overall_status": status,
                "overall_success": overall_success,
                "mcp_result": mcp_result,
                "rest_result": rest_result
            }
    
    async def simulate_authentication_scenario(self, server_name: str):
        """Simulate authentication scenarios with token refresh."""
        context = LogContext(
            server_name=server_name,
            operation_type=OperationType.AUTHENTICATION
        )
        
        with self.logger.push_context(context):
            try:
                self.logger.info(f"Authenticating with {server_name}")
                
                # Simulate token expiration
                raise Exception("Token expired")
                
            except Exception as e:
                error_context = ErrorContext(
                    server_name=server_name,
                    operation="authentication"
                )
                
                auth_data = {
                    "auth_type": "jwt",
                    "token_type": "bearer",
                    "expires_at": datetime.utcnow() - timedelta(hours=1)
                }
                
                error = self.error_handler.handle_authentication_error(
                    e, error_context, auth_data
                )
                
                self.logger.log_error(error)
                self.analyzer.add_error(error)
                
                # Simulate token refresh
                self.logger.log_authentication(
                    auth_method="jwt_refresh",
                    success=True,
                    token_type="bearer",
                    expires_in_seconds=3600
                )
                
                return {"success": True, "action": "token_refreshed"}
    
    async def run_comprehensive_simulation(self):
        """Run comprehensive simulation with various scenarios."""
        print("🚀 Starting comprehensive error handling and logging simulation...")
        
        servers = ["server-1", "server-2", "server-3", "server-4"]
        
        # Scenario 1: Normal operations
        print("\n📊 Scenario 1: Normal operations")
        for server in servers[:2]:
            result = await self.simulate_dual_health_check(server)
            print(f"  ✅ {server}: {result['overall_status']}")
        
        # Scenario 2: MCP failures
        print("\n⚠️  Scenario 2: MCP failures")
        for server in servers[2:]:
            result = await self.simulate_dual_health_check(
                server, mcp_should_fail=True
            )
            print(f"  🔴 {server}: {result['overall_status']} (MCP failed)")
        
        # Scenario 3: REST failures
        print("\n🌐 Scenario 3: REST failures")
        for server in servers[:2]:
            result = await self.simulate_dual_health_check(
                server, rest_should_fail=True
            )
            print(f"  🟡 {server}: {result['overall_status']} (REST failed)")
        
        # Scenario 4: Authentication issues
        print("\n🔐 Scenario 4: Authentication scenarios")
        for server in servers[::2]:  # Every other server
            result = await self.simulate_authentication_scenario(server)
            print(f"  🔄 {server}: {result['action']}")
        
        # Scenario 5: High-frequency errors (pattern detection)
        print("\n🔥 Scenario 5: High-frequency error pattern")
        for i in range(8):
            await self.simulate_mcp_health_check("problematic-server", should_fail=True)
            await asyncio.sleep(0.1)  # Small delay between errors
        
        print("  🔍 Generated high-frequency error pattern")
        
        # Analyze results
        await self.analyze_and_report()
    
    async def analyze_and_report(self):
        """Analyze errors and generate comprehensive report."""
        print("\n📈 Analyzing errors and generating report...")
        
        # Get error statistics
        stats = self.analyzer.get_error_statistics(time_window_hours=1)
        print(f"\n📊 Error Statistics:")
        print(f"  Total errors: {stats['total_errors']}")
        print(f"  Error rate: {stats['error_rate']:.2f} errors/hour")
        print(f"  Recovery rate: {stats['recovery_rate']:.2%}")
        
        # Show most common errors
        print(f"\n🔝 Most Common Errors:")
        for error_info in stats['most_common_errors'][:3]:
            print(f"  {error_info['error_code']}: {error_info['count']} ({error_info['percentage']:.1f}%)")
        
        # Analyze patterns
        patterns = self.analyzer.analyze_error_patterns(time_window_hours=1)
        print(f"\n🔍 Detected Patterns: {len(patterns)}")
        
        for pattern in patterns[:3]:  # Show top 3 patterns
            print(f"  {pattern.pattern_type.upper()}: {pattern.description}")
            print(f"    Confidence: {pattern.confidence_score:.2f}")
            print(f"    Servers: {', '.join(pattern.servers_affected)}")
            if pattern.recommended_actions:
                print(f"    Actions: {pattern.recommended_actions[0]}")
        
        # Generate system health assessment
        assessment = self.analyzer.assess_system_health(time_window_hours=1)
        print(f"\n🏥 System Health Assessment:")
        print(f"  Overall Health Score: {assessment.overall_health_score:.2f}/1.0")
        
        if assessment.critical_issues:
            print(f"  🚨 Critical Issues:")
            for issue in assessment.critical_issues:
                print(f"    - {issue}")
        
        if assessment.warnings:
            print(f"  ⚠️  Warnings:")
            for warning in assessment.warnings:
                print(f"    - {warning}")
        
        # Show recommendations
        print(f"\n💡 Recommendations: {len(assessment.recommendations)}")
        for rec in assessment.recommendations[:3]:  # Show top 3 recommendations
            print(f"  {rec.priority.upper()}: {rec.title}")
            print(f"    {rec.description}")
            print(f"    Estimated time: {rec.estimated_time_minutes} minutes")
        
        # Show server health scores
        print(f"\n🖥️  Server Health Scores:")
        for server, score in assessment.server_health_scores.items():
            status = "🟢" if score > 0.8 else "🟡" if score > 0.5 else "🔴"
            print(f"  {status} {server}: {score:.2f}")
        
        # Show trend analysis
        trend = assessment.trend_analysis
        if trend.get("trend") != "insufficient_data":
            trend_emoji = "📈" if trend["trend"] == "increasing" else "📉" if trend["trend"] == "decreasing" else "➡️"
            print(f"\n{trend_emoji} Trend Analysis: {trend['trend']}")
            print(f"  Recent error rate: {trend.get('recent_error_rate', 0)}")
            print(f"  Average error rate: {trend.get('average_error_rate', 0):.2f}")
    
    def generate_json_report(self, output_file: str = "error_analysis_report.json"):
        """Generate detailed JSON report."""
        assessment = self.analyzer.assess_system_health(time_window_hours=1)
        stats = self.analyzer.get_error_statistics(time_window_hours=1)
        patterns = self.analyzer.analyze_error_patterns(time_window_hours=1)
        
        report = {
            "report_metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "time_window_hours": 1,
                "report_version": "1.0"
            },
            "system_health_assessment": assessment.to_dict(),
            "error_statistics": stats,
            "error_patterns": [p.to_dict() for p in patterns],
            "error_history": [e.to_dict() for e in self.analyzer.error_history[-20:]]  # Last 20 errors
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n📄 Detailed report saved to: {output_file}")


async def main():
    """Main function to run the comprehensive example."""
    # Create logs directory
    Path("logs").mkdir(exist_ok=True)
    
    # Create and run simulator
    simulator = DualMonitoringSimulator()
    
    try:
        await simulator.run_comprehensive_simulation()
        
        # Generate detailed JSON report
        simulator.generate_json_report("logs/comprehensive_error_analysis_report.json")
        
        print("\n✅ Comprehensive error handling and logging simulation completed!")
        print("📁 Check the 'logs' directory for detailed logs and reports.")
        
    except Exception as e:
        print(f"\n❌ Simulation failed: {e}")
        raise
    
    finally:
        # Flush and close all log outputs
        simulator.logger.flush_all()


if __name__ == "__main__":
    asyncio.run(main())