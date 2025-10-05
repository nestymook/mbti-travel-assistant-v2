"""
Enhanced MCP Status Check Dual Metrics Collector Example

This example demonstrates how to use the DualMetricsCollector to collect
and analyze metrics from both MCP tools/list requests and REST health checks.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import (
    DualHealthCheckResult, MCPHealthCheckResult, RESTHealthCheckResult,
    ServerStatus, MCPValidationResult, RESTValidationResult,
    EnhancedServerConfig, TimeWindow
)
from services.dual_metrics_collector import DualMetricsCollector


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_sample_mcp_result(server_name: str, success: bool = True, response_time: float = 150.0) -> MCPHealthCheckResult:
    """Create a sample MCP health check result."""
    if success:
        return MCPHealthCheckResult(
            server_name=server_name,
            timestamp=datetime.now(),
            success=True,
            response_time_ms=response_time,
            tools_count=5,
            expected_tools_found=["search_restaurants", "recommend_restaurants", "get_districts"],
            missing_tools=[],
            validation_result=MCPValidationResult(
                is_valid=True,
                tools_count=5,
                expected_tools_found=["search_restaurants", "recommend_restaurants", "get_districts"],
                missing_tools=[],
                validation_errors=[]
            ),
            request_id=f"mcp-request-{datetime.now().timestamp()}"
        )
    else:
        return MCPHealthCheckResult(
            server_name=server_name,
            timestamp=datetime.now(),
            success=False,
            response_time_ms=response_time,
            connection_error="Connection timeout",
            mcp_error={"code": -32000, "message": "Request timeout"}
        )


def create_sample_rest_result(server_name: str, success: bool = True, response_time: float = 120.0) -> RESTHealthCheckResult:
    """Create a sample REST health check result."""
    if success:
        return RESTHealthCheckResult(
            server_name=server_name,
            timestamp=datetime.now(),
            success=True,
            response_time_ms=response_time,
            status_code=200,
            response_body={
                "status": "healthy",
                "uptime": 3600,
                "version": "1.0.0",
                "checks": {
                    "database": "ok",
                    "cache": "ok"
                }
            },
            health_endpoint_url=f"http://{server_name}/status/health",
            validation_result=RESTValidationResult(
                is_valid=True,
                http_status_valid=True,
                response_format_valid=True,
                health_indicators_present=True,
                validation_errors=[]
            )
        )
    else:
        return RESTHealthCheckResult(
            server_name=server_name,
            timestamp=datetime.now(),
            success=False,
            response_time_ms=response_time,
            status_code=500,
            response_body={"error": "Internal server error"},
            health_endpoint_url=f"http://{server_name}/status/health",
            http_error="Internal Server Error"
        )


def create_sample_dual_result(server_name: str, mcp_success: bool = True, rest_success: bool = True) -> DualHealthCheckResult:
    """Create a sample dual health check result."""
    mcp_result = create_sample_mcp_result(server_name, mcp_success)
    rest_result = create_sample_rest_result(server_name, rest_success)
    
    # Determine overall status
    if mcp_success and rest_success:
        overall_status = ServerStatus.HEALTHY
        overall_success = True
        health_score = 1.0
        available_paths = ["mcp", "rest"]
    elif mcp_success or rest_success:
        overall_status = ServerStatus.DEGRADED
        overall_success = False
        health_score = 0.5
        available_paths = ["mcp"] if mcp_success else ["rest"]
    else:
        overall_status = ServerStatus.UNHEALTHY
        overall_success = False
        health_score = 0.0
        available_paths = []
    
    combined_response_time = (mcp_result.response_time_ms + rest_result.response_time_ms) / 2
    
    return DualHealthCheckResult(
        server_name=server_name,
        timestamp=datetime.now(),
        overall_status=overall_status,
        overall_success=overall_success,
        mcp_result=mcp_result,
        mcp_success=mcp_success,
        mcp_response_time_ms=mcp_result.response_time_ms,
        mcp_tools_count=mcp_result.tools_count,
        rest_result=rest_result,
        rest_success=rest_success,
        rest_response_time_ms=rest_result.response_time_ms,
        rest_status_code=rest_result.status_code,
        combined_response_time_ms=combined_response_time,
        health_score=health_score,
        available_paths=available_paths
    )


async def simulate_health_checks(collector: DualMetricsCollector, servers: List[str], duration_minutes: int = 5):
    """
    Simulate health checks for multiple servers over a period of time.
    
    Args:
        collector: The metrics collector instance
        servers: List of server names to simulate
        duration_minutes: How long to run the simulation
    """
    logger.info("Starting health check simulation for %d servers over %d minutes", len(servers), duration_minutes)
    
    end_time = datetime.now() + timedelta(minutes=duration_minutes)
    check_interval = 30  # seconds
    
    while datetime.now() < end_time:
        for server_name in servers:
            # Simulate varying success rates and response times
            import random
            
            # 90% success rate for MCP, 85% for REST
            mcp_success = random.random() < 0.90
            rest_success = random.random() < 0.85
            
            # Varying response times
            mcp_response_time = random.uniform(50, 300)
            rest_response_time = random.uniform(40, 250)
            
            # Create and record dual result
            dual_result = create_sample_dual_result(server_name, mcp_success, rest_success)
            dual_result.mcp_result.response_time_ms = mcp_response_time
            dual_result.rest_result.response_time_ms = rest_response_time
            dual_result.combined_response_time_ms = (mcp_response_time + rest_response_time) / 2
            
            collector.record_dual_health_check_result(dual_result)
            
            logger.debug("Recorded health check for %s: MCP=%s, REST=%s", 
                        server_name, mcp_success, rest_success)
        
        # Wait before next check
        await asyncio.sleep(check_interval)
    
    logger.info("Health check simulation completed")


def print_metrics_summary(collector: DualMetricsCollector):
    """Print a summary of collected metrics."""
    print("\n" + "="*80)
    print("METRICS COLLECTION SUMMARY")
    print("="*80)
    
    summary = collector.get_metrics_summary()
    
    print(f"Total Servers Monitored: {summary['total_servers_monitored']}")
    print(f"MCP Servers: {summary['mcp_servers_count']}")
    print(f"REST Servers: {summary['rest_servers_count']}")
    print(f"Combined Servers: {summary['combined_servers_count']}")
    print(f"Retention Period: {summary['retention_period_days']} days")
    print(f"Collection Time: {summary['collection_timestamp']}")
    
    print("\nPER-SERVER SUMMARY:")
    print("-" * 80)
    
    for server_name, server_summary in summary['servers'].items():
        print(f"\nServer: {server_name}")
        print(f"  MCP Enabled: {server_summary['mcp_enabled']}")
        print(f"  REST Enabled: {server_summary['rest_enabled']}")
        print(f"  MCP Requests: {server_summary['mcp_total_requests']}")
        print(f"  REST Requests: {server_summary['rest_total_requests']}")
        print(f"  MCP Success Rate: {server_summary['mcp_success_rate']:.2%}")
        print(f"  REST Success Rate: {server_summary['rest_success_rate']:.2%}")


def print_detailed_server_report(collector: DualMetricsCollector, server_name: str):
    """Print detailed metrics report for a specific server."""
    print(f"\n" + "="*80)
    print(f"DETAILED METRICS REPORT - {server_name}")
    print("="*80)
    
    # Generate aggregation report
    report = collector.generate_aggregation_report(server_name, TimeWindow.LAST_HOUR)
    
    if not report:
        print(f"No metrics found for server: {server_name}")
        return
    
    print(f"Report Time: {report.report_timestamp}")
    print(f"Time Window: {report.time_window.value}")
    
    print("\nMCP METRICS:")
    print("-" * 40)
    print(f"  Success Rate: {report.mcp_success_rate:.2%}")
    print(f"  Average Response Time: {report.mcp_average_response_time:.1f}ms")
    print(f"  95th Percentile Response Time: {report.mcp_p95_response_time:.1f}ms")
    print(f"  Tools Availability Rate: {report.mcp_tools_availability_rate:.2%}")
    
    print("\nREST METRICS:")
    print("-" * 40)
    print(f"  Success Rate: {report.rest_success_rate:.2%}")
    print(f"  Average Response Time: {report.rest_average_response_time:.1f}ms")
    print(f"  95th Percentile Response Time: {report.rest_p95_response_time:.1f}ms")
    print(f"  Endpoint Availability Rate: {report.rest_endpoint_availability_rate:.2%}")
    
    print("\nCOMBINED METRICS:")
    print("-" * 40)
    print(f"  Combined Success Rate: {report.combined_success_rate:.2%}")
    print(f"  Combined Average Response Time: {report.combined_average_response_time:.1f}ms")
    print(f"  Overall Availability Rate: {report.overall_availability_rate:.2%}")
    
    if report.top_http_status_codes:
        print("\nTOP HTTP STATUS CODES:")
        print("-" * 40)
        for status_code, count in report.top_http_status_codes:
            print(f"  {status_code}: {count} occurrences")
    
    if report.error_breakdown:
        print("\nERROR BREAKDOWN:")
        print("-" * 40)
        for error_type, count in report.error_breakdown.items():
            print(f"  {error_type}: {count}")


def demonstrate_individual_metrics(collector: DualMetricsCollector):
    """Demonstrate recording individual MCP and REST metrics."""
    print("\n" + "="*80)
    print("INDIVIDUAL METRICS DEMONSTRATION")
    print("="*80)
    
    server_name = "demo-server"
    
    # Record individual MCP results
    print("\nRecording individual MCP health check results...")
    for i in range(3):
        mcp_result = create_sample_mcp_result(
            server_name, 
            success=(i < 2),  # First 2 succeed, last one fails
            response_time=100 + i * 50
        )
        collector.record_mcp_health_check_result(mcp_result)
        print(f"  MCP Check {i+1}: Success={mcp_result.success}, Time={mcp_result.response_time_ms}ms")
    
    # Record individual REST results
    print("\nRecording individual REST health check results...")
    for i in range(3):
        rest_result = create_sample_rest_result(
            server_name,
            success=(i != 1),  # First and third succeed, second fails
            response_time=80 + i * 40
        )
        collector.record_rest_health_check_result(rest_result)
        print(f"  REST Check {i+1}: Success={rest_result.success}, Time={rest_result.response_time_ms}ms")
    
    # Show individual metrics
    mcp_metrics = collector.get_mcp_metrics(server_name)
    rest_metrics = collector.get_rest_metrics(server_name)
    
    print(f"\nMCP Metrics Summary:")
    print(f"  Total Requests: {mcp_metrics.total_requests}")
    print(f"  Success Rate: {mcp_metrics.get_success_rate():.2%}")
    print(f"  Average Response Time: {mcp_metrics.get_average_response_time():.1f}ms")
    
    print(f"\nREST Metrics Summary:")
    print(f"  Total Requests: {rest_metrics.total_requests}")
    print(f"  Success Rate: {rest_metrics.get_success_rate():.2%}")
    print(f"  Average Response Time: {rest_metrics.get_average_response_time():.1f}ms")


def demonstrate_export_import(collector: DualMetricsCollector):
    """Demonstrate exporting and importing metrics data."""
    print("\n" + "="*80)
    print("EXPORT/IMPORT DEMONSTRATION")
    print("="*80)
    
    # Record some sample data
    servers = ["export-server-1", "export-server-2"]
    for server_name in servers:
        dual_result = create_sample_dual_result(server_name)
        collector.record_dual_health_check_result(dual_result)
    
    print(f"Recorded metrics for {len(servers)} servers")
    
    # Export data
    export_data = collector.export_metrics_data()
    print(f"Exported metrics data: {len(export_data['mcp_metrics'])} MCP servers, "
          f"{len(export_data['rest_metrics'])} REST servers")
    
    # Reset metrics
    original_server_count = len(collector.get_all_server_names())
    collector.reset_metrics()
    print(f"Reset all metrics (was {original_server_count} servers, now {len(collector.get_all_server_names())})")
    
    # Import data back
    collector.import_metrics_data(export_data)
    restored_server_count = len(collector.get_all_server_names())
    print(f"Imported metrics data: restored {restored_server_count} servers")
    
    # Verify data integrity
    for server_name in servers:
        mcp_metrics = collector.get_mcp_metrics(server_name)
        rest_metrics = collector.get_rest_metrics(server_name)
        print(f"  {server_name}: MCP requests={mcp_metrics.total_requests}, "
              f"REST requests={rest_metrics.total_requests}")


async def main():
    """Main example function."""
    print("Enhanced MCP Status Check - Dual Metrics Collector Example")
    print("=" * 80)
    
    # Create metrics collector with 1-hour retention
    collector = DualMetricsCollector(retention_period=timedelta(hours=1))
    
    try:
        # Start the collector
        await collector.start()
        print("Started DualMetricsCollector")
        
        # Demonstrate individual metrics recording
        demonstrate_individual_metrics(collector)
        
        # Demonstrate export/import functionality
        demonstrate_export_import(collector)
        
        # Simulate health checks for multiple servers
        servers = [
            "restaurant-search-mcp",
            "restaurant-reasoning-mcp", 
            "mbti-travel-assistant-mcp"
        ]
        
        print(f"\nStarting health check simulation for servers: {', '.join(servers)}")
        await simulate_health_checks(collector, servers, duration_minutes=2)
        
        # Print metrics summary
        print_metrics_summary(collector)
        
        # Print detailed reports for each server
        for server_name in servers:
            print_detailed_server_report(collector, server_name)
        
        # Generate reports for all servers
        print("\n" + "="*80)
        print("ALL SERVERS AGGREGATION REPORTS")
        print("="*80)
        
        all_reports = collector.generate_all_servers_report(TimeWindow.LAST_HOUR)
        print(f"Generated {len(all_reports)} server reports")
        
        for report in all_reports:
            print(f"\n{report.server_name}:")
            print(f"  Combined Success Rate: {report.combined_success_rate:.2%}")
            print(f"  Combined Avg Response Time: {report.combined_average_response_time:.1f}ms")
            print(f"  Overall Availability: {report.overall_availability_rate:.2%}")
        
        # Demonstrate cleanup
        print("\n" + "="*80)
        print("CLEANUP DEMONSTRATION")
        print("="*80)
        
        print("Performing metrics cleanup...")
        collector.cleanup_old_metrics()
        print("Cleanup completed")
        
        # Show final summary
        final_summary = collector.get_metrics_summary()
        print(f"Final server count: {final_summary['total_servers_monitored']}")
        
    finally:
        # Stop the collector
        await collector.stop()
        print("\nStopped DualMetricsCollector")


if __name__ == "__main__":
    # Run the example
    asyncio.run(main())