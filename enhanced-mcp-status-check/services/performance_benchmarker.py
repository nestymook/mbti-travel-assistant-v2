"""
Performance benchmarking and optimization testing service.

This module provides comprehensive performance testing and benchmarking
capabilities for the enhanced MCP status check system.

Requirements: 10.5
"""

import asyncio
import time
import statistics
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
import json
import csv
from concurrent.futures import ThreadPoolExecutor
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

try:
    from ..models.dual_health_models import (
        DualHealthCheckResult,
        EnhancedServerConfig
    )
    from .performance_optimizer import (
        PerformanceOptimizer,
        PerformanceMetrics,
        ConnectionPoolConfig,
        ResourceLimits,
        CacheConfig
    )
except ImportError:
    # For direct execution, use absolute imports
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from models.dual_health_models import (
        DualHealthCheckResult,
        EnhancedServerConfig
    )
    from services.performance_optimizer import (
        PerformanceOptimizer,
        PerformanceMetrics,
        ConnectionPoolConfig,
        ResourceLimits,
        CacheConfig
    )


@dataclass
class BenchmarkConfig:
    """Configuration for performance benchmarks."""
    name: str
    description: str
    duration_seconds: int = 60
    concurrent_users: List[int] = field(default_factory=lambda: [1, 5, 10, 20, 50])
    server_counts: List[int] = field(default_factory=lambda: [1, 5, 10, 25, 50])
    warmup_duration: int = 10
    cooldown_duration: int = 5
    iterations: int = 3
    output_dir: str = "benchmark_results"


@dataclass
class BenchmarkResult:
    """Results from a performance benchmark."""
    config_name: str
    timestamp: datetime
    concurrent_users: int
    server_count: int
    iteration: int
    
    # Performance metrics
    total_requests: int
    successful_requests: int
    failed_requests: int
    requests_per_second: float
    average_response_time_ms: float
    median_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    min_response_time_ms: float
    max_response_time_ms: float
    
    # Resource metrics
    peak_memory_usage_mb: float
    average_cpu_usage_percent: float
    peak_cpu_usage_percent: float
    connection_pool_utilization: float
    cache_hit_rate: float
    
    # Error metrics
    timeout_errors: int
    connection_errors: int
    authentication_errors: int
    other_errors: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'config_name': self.config_name,
            'timestamp': self.timestamp.isoformat(),
            'concurrent_users': self.concurrent_users,
            'server_count': self.server_count,
            'iteration': self.iteration,
            'total_requests': self.total_requests,
            'successful_requests': self.successful_requests,
            'failed_requests': self.failed_requests,
            'requests_per_second': self.requests_per_second,
            'average_response_time_ms': self.average_response_time_ms,
            'median_response_time_ms': self.median_response_time_ms,
            'p95_response_time_ms': self.p95_response_time_ms,
            'p99_response_time_ms': self.p99_response_time_ms,
            'min_response_time_ms': self.min_response_time_ms,
            'max_response_time_ms': self.max_response_time_ms,
            'peak_memory_usage_mb': self.peak_memory_usage_mb,
            'average_cpu_usage_percent': self.average_cpu_usage_percent,
            'peak_cpu_usage_percent': self.peak_cpu_usage_percent,
            'connection_pool_utilization': self.connection_pool_utilization,
            'cache_hit_rate': self.cache_hit_rate,
            'timeout_errors': self.timeout_errors,
            'connection_errors': self.connection_errors,
            'authentication_errors': self.authentication_errors,
            'other_errors': self.other_errors
        }


@dataclass
class LoadTestScenario:
    """Defines a load testing scenario."""
    name: str
    description: str
    concurrent_users: int
    duration_seconds: int
    ramp_up_seconds: int = 10
    ramp_down_seconds: int = 10
    think_time_ms: int = 1000
    server_configs: List[EnhancedServerConfig] = field(default_factory=list)


class PerformanceBenchmarker:
    """Performance benchmarking and testing service."""
    
    def __init__(self, optimizer: PerformanceOptimizer):
        self.optimizer = optimizer
        self.logger = logging.getLogger(__name__)
        self._benchmark_results: List[BenchmarkResult] = []
        
    async def run_benchmark_suite(
        self,
        configs: List[BenchmarkConfig],
        health_check_func: Callable,
        server_configs: List[EnhancedServerConfig]
    ) -> List[BenchmarkResult]:
        """Run a complete benchmark suite."""
        all_results = []
        
        for config in configs:
            self.logger.info(f"Starting benchmark: {config.name}")
            
            results = await self.run_benchmark(
                config, health_check_func, server_configs
            )
            all_results.extend(results)
            
            # Save intermediate results
            await self._save_results(results, config.output_dir)
            
        self._benchmark_results.extend(all_results)
        return all_results
        
    async def run_benchmark(
        self,
        config: BenchmarkConfig,
        health_check_func: Callable,
        server_configs: List[EnhancedServerConfig]
    ) -> List[BenchmarkResult]:
        """Run a single benchmark configuration."""
        results = []
        
        for concurrent_users in config.concurrent_users:
            for server_count in config.server_counts:
                # Limit server configs to the specified count
                test_servers = server_configs[:server_count]
                
                for iteration in range(config.iterations):
                    self.logger.info(
                        f"Running {config.name} - "
                        f"Users: {concurrent_users}, "
                        f"Servers: {server_count}, "
                        f"Iteration: {iteration + 1}/{config.iterations}"
                    )
                    
                    result = await self._run_single_benchmark(
                        config, concurrent_users, test_servers,
                        health_check_func, iteration
                    )
                    
                    results.append(result)
                    
                    # Cooldown between iterations
                    if iteration < config.iterations - 1:
                        await asyncio.sleep(config.cooldown_duration)
                        
        return results
        
    async def _run_single_benchmark(
        self,
        config: BenchmarkConfig,
        concurrent_users: int,
        server_configs: List[EnhancedServerConfig],
        health_check_func: Callable,
        iteration: int
    ) -> BenchmarkResult:
        """Run a single benchmark iteration."""
        # Warmup phase
        if config.warmup_duration > 0:
            self.logger.debug("Starting warmup phase")
            await self._run_load_phase(
                concurrent_users, server_configs, health_check_func,
                config.warmup_duration, collect_metrics=False
            )
            
        # Main benchmark phase
        self.logger.debug("Starting main benchmark phase")
        start_time = time.time()
        
        metrics_collector = MetricsCollector()
        await metrics_collector.start()
        
        try:
            response_times, error_counts = await self._run_load_phase(
                concurrent_users, server_configs, health_check_func,
                config.duration_seconds, collect_metrics=True
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Collect final metrics
            final_metrics = await metrics_collector.get_final_metrics()
            
            # Calculate statistics
            total_requests = len(response_times) + sum(error_counts.values())
            successful_requests = len(response_times)
            failed_requests = sum(error_counts.values())
            
            if response_times:
                avg_response_time = statistics.mean(response_times)
                median_response_time = statistics.median(response_times)
                p95_response_time = np.percentile(response_times, 95)
                p99_response_time = np.percentile(response_times, 99)
                min_response_time = min(response_times)
                max_response_time = max(response_times)
            else:
                avg_response_time = 0
                median_response_time = 0
                p95_response_time = 0
                p99_response_time = 0
                min_response_time = 0
                max_response_time = 0
                
            requests_per_second = total_requests / duration if duration > 0 else 0
            
            return BenchmarkResult(
                config_name=config.name,
                timestamp=datetime.now(),
                concurrent_users=concurrent_users,
                server_count=len(server_configs),
                iteration=iteration,
                total_requests=total_requests,
                successful_requests=successful_requests,
                failed_requests=failed_requests,
                requests_per_second=requests_per_second,
                average_response_time_ms=avg_response_time,
                median_response_time_ms=median_response_time,
                p95_response_time_ms=p95_response_time,
                p99_response_time_ms=p99_response_time,
                min_response_time_ms=min_response_time,
                max_response_time_ms=max_response_time,
                peak_memory_usage_mb=final_metrics['peak_memory_mb'],
                average_cpu_usage_percent=final_metrics['avg_cpu_percent'],
                peak_cpu_usage_percent=final_metrics['peak_cpu_percent'],
                connection_pool_utilization=final_metrics['pool_utilization'],
                cache_hit_rate=final_metrics['cache_hit_rate'],
                timeout_errors=error_counts.get('timeout', 0),
                connection_errors=error_counts.get('connection', 0),
                authentication_errors=error_counts.get('auth', 0),
                other_errors=error_counts.get('other', 0)
            )
            
        finally:
            await metrics_collector.stop()
            
    async def _run_load_phase(
        self,
        concurrent_users: int,
        server_configs: List[EnhancedServerConfig],
        health_check_func: Callable,
        duration_seconds: int,
        collect_metrics: bool = True
    ) -> Tuple[List[float], Dict[str, int]]:
        """Run a load testing phase."""
        response_times = []
        error_counts = {
            'timeout': 0,
            'connection': 0,
            'auth': 0,
            'other': 0
        }
        
        end_time = time.time() + duration_seconds
        
        async def user_simulation():
            """Simulate a single user's load."""
            user_response_times = []
            user_errors = {'timeout': 0, 'connection': 0, 'auth': 0, 'other': 0}
            
            while time.time() < end_time:
                try:
                    start_time = time.time()
                    
                    # Execute health checks for all servers
                    results = await self.optimizer.execute_concurrent_health_checks(
                        server_configs, health_check_func
                    )
                    
                    response_time = (time.time() - start_time) * 1000
                    user_response_times.append(response_time)
                    
                except asyncio.TimeoutError:
                    user_errors['timeout'] += 1
                except ConnectionError:
                    user_errors['connection'] += 1
                except Exception as e:
                    if 'auth' in str(e).lower():
                        user_errors['auth'] += 1
                    else:
                        user_errors['other'] += 1
                        
                # Small delay between requests
                await asyncio.sleep(0.1)
                
            return user_response_times, user_errors
            
        # Run concurrent user simulations
        tasks = [user_simulation() for _ in range(concurrent_users)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Aggregate results
        for result in results:
            if isinstance(result, Exception):
                error_counts['other'] += 1
                continue
                
            user_times, user_errors = result
            response_times.extend(user_times)
            
            for error_type, count in user_errors.items():
                error_counts[error_type] += count
                
        return response_times, error_counts
        
    async def run_load_test(
        self,
        scenario: LoadTestScenario,
        health_check_func: Callable
    ) -> BenchmarkResult:
        """Run a specific load test scenario."""
        self.logger.info(f"Starting load test: {scenario.name}")
        
        # Ramp up phase
        if scenario.ramp_up_seconds > 0:
            await self._ramp_up_load(
                scenario.concurrent_users, scenario.server_configs,
                health_check_func, scenario.ramp_up_seconds
            )
            
        # Main load phase
        start_time = time.time()
        response_times, error_counts = await self._run_load_phase(
            scenario.concurrent_users, scenario.server_configs,
            health_check_func, scenario.duration_seconds
        )
        end_time = time.time()
        
        # Ramp down phase
        if scenario.ramp_down_seconds > 0:
            await self._ramp_down_load(scenario.ramp_down_seconds)
            
        # Calculate results
        duration = end_time - start_time
        total_requests = len(response_times) + sum(error_counts.values())
        
        return BenchmarkResult(
            config_name=scenario.name,
            timestamp=datetime.now(),
            concurrent_users=scenario.concurrent_users,
            server_count=len(scenario.server_configs),
            iteration=0,
            total_requests=total_requests,
            successful_requests=len(response_times),
            failed_requests=sum(error_counts.values()),
            requests_per_second=total_requests / duration if duration > 0 else 0,
            average_response_time_ms=statistics.mean(response_times) if response_times else 0,
            median_response_time_ms=statistics.median(response_times) if response_times else 0,
            p95_response_time_ms=np.percentile(response_times, 95) if response_times else 0,
            p99_response_time_ms=np.percentile(response_times, 99) if response_times else 0,
            min_response_time_ms=min(response_times) if response_times else 0,
            max_response_time_ms=max(response_times) if response_times else 0,
            peak_memory_usage_mb=0,  # Would be collected by metrics collector
            average_cpu_usage_percent=0,
            peak_cpu_usage_percent=0,
            connection_pool_utilization=0,
            cache_hit_rate=0,
            timeout_errors=error_counts.get('timeout', 0),
            connection_errors=error_counts.get('connection', 0),
            authentication_errors=error_counts.get('auth', 0),
            other_errors=error_counts.get('other', 0)
        )
        
    async def _ramp_up_load(
        self,
        target_users: int,
        server_configs: List[EnhancedServerConfig],
        health_check_func: Callable,
        ramp_up_seconds: int
    ):
        """Gradually ramp up load to target users."""
        steps = min(10, target_users)  # Max 10 steps
        users_per_step = target_users // steps
        step_duration = ramp_up_seconds / steps
        
        current_users = 0
        
        for step in range(steps):
            current_users += users_per_step
            if step == steps - 1:  # Last step
                current_users = target_users
                
            self.logger.debug(f"Ramping up to {current_users} users")
            
            # Start additional user tasks
            # (Implementation would depend on task management)
            
            await asyncio.sleep(step_duration)
            
    async def _ramp_down_load(self, ramp_down_seconds: int):
        """Gradually ramp down load."""
        # Implementation would gradually reduce active tasks
        await asyncio.sleep(ramp_down_seconds)
        
    async def _save_results(
        self,
        results: List[BenchmarkResult],
        output_dir: str
    ):
        """Save benchmark results to files."""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save as JSON
        json_file = output_path / f"benchmark_results_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(
                [result.to_dict() for result in results],
                f, indent=2, default=str
            )
            
        # Save as CSV
        csv_file = output_path / f"benchmark_results_{timestamp}.csv"
        with open(csv_file, 'w', newline='') as f:
            if results:
                writer = csv.DictWriter(f, fieldnames=results[0].to_dict().keys())
                writer.writeheader()
                for result in results:
                    writer.writerow(result.to_dict())
                    
        self.logger.info(f"Results saved to {json_file} and {csv_file}")
        
    def generate_performance_report(
        self,
        results: List[BenchmarkResult],
        output_dir: str = "reports"
    ) -> str:
        """Generate a comprehensive performance report."""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = output_path / f"performance_report_{timestamp}.html"
        
        # Generate charts
        charts_dir = output_path / "charts"
        charts_dir.mkdir(exist_ok=True)
        
        self._generate_performance_charts(results, str(charts_dir))
        
        # Generate HTML report
        html_content = self._generate_html_report(results, str(charts_dir))
        
        with open(report_file, 'w') as f:
            f.write(html_content)
            
        self.logger.info(f"Performance report generated: {report_file}")
        return str(report_file)
        
    def _generate_performance_charts(
        self,
        results: List[BenchmarkResult],
        charts_dir: str
    ):
        """Generate performance charts."""
        charts_path = Path(charts_dir)
        
        # Response time vs concurrent users
        plt.figure(figsize=(12, 8))
        
        configs = list(set(r.config_name for r in results))
        for config in configs:
            config_results = [r for r in results if r.config_name == config]
            users = [r.concurrent_users for r in config_results]
            response_times = [r.average_response_time_ms for r in config_results]
            
            plt.plot(users, response_times, marker='o', label=config)
            
        plt.xlabel('Concurrent Users')
        plt.ylabel('Average Response Time (ms)')
        plt.title('Response Time vs Concurrent Users')
        plt.legend()
        plt.grid(True)
        plt.savefig(charts_path / 'response_time_vs_users.png')
        plt.close()
        
        # Throughput vs concurrent users
        plt.figure(figsize=(12, 8))
        
        for config in configs:
            config_results = [r for r in results if r.config_name == config]
            users = [r.concurrent_users for r in config_results]
            throughput = [r.requests_per_second for r in config_results]
            
            plt.plot(users, throughput, marker='o', label=config)
            
        plt.xlabel('Concurrent Users')
        plt.ylabel('Requests per Second')
        plt.title('Throughput vs Concurrent Users')
        plt.legend()
        plt.grid(True)
        plt.savefig(charts_path / 'throughput_vs_users.png')
        plt.close()
        
        # Error rate analysis
        plt.figure(figsize=(12, 8))
        
        for config in configs:
            config_results = [r for r in results if r.config_name == config]
            users = [r.concurrent_users for r in config_results]
            error_rates = [
                (r.failed_requests / r.total_requests * 100) if r.total_requests > 0 else 0
                for r in config_results
            ]
            
            plt.plot(users, error_rates, marker='o', label=config)
            
        plt.xlabel('Concurrent Users')
        plt.ylabel('Error Rate (%)')
        plt.title('Error Rate vs Concurrent Users')
        plt.legend()
        plt.grid(True)
        plt.savefig(charts_path / 'error_rate_vs_users.png')
        plt.close()
        
    def _generate_html_report(
        self,
        results: List[BenchmarkResult],
        charts_dir: str
    ) -> str:
        """Generate HTML performance report."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Performance Benchmark Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; }}
                .section {{ margin: 20px 0; }}
                .chart {{ text-align: center; margin: 20px 0; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .metric {{ display: inline-block; margin: 10px; padding: 10px; 
                          background-color: #e9e9e9; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Performance Benchmark Report</h1>
                <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>Total Benchmarks: {len(results)}</p>
            </div>
            
            <div class="section">
                <h2>Executive Summary</h2>
                {self._generate_summary_metrics(results)}
            </div>
            
            <div class="section">
                <h2>Performance Charts</h2>
                <div class="chart">
                    <h3>Response Time vs Concurrent Users</h3>
                    <img src="charts/response_time_vs_users.png" alt="Response Time Chart">
                </div>
                <div class="chart">
                    <h3>Throughput vs Concurrent Users</h3>
                    <img src="charts/throughput_vs_users.png" alt="Throughput Chart">
                </div>
                <div class="chart">
                    <h3>Error Rate vs Concurrent Users</h3>
                    <img src="charts/error_rate_vs_users.png" alt="Error Rate Chart">
                </div>
            </div>
            
            <div class="section">
                <h2>Detailed Results</h2>
                {self._generate_results_table(results)}
            </div>
            
            <div class="section">
                <h2>Recommendations</h2>
                {self._generate_recommendations(results)}
            </div>
        </body>
        </html>
        """
        
        return html
        
    def _generate_summary_metrics(self, results: List[BenchmarkResult]) -> str:
        """Generate summary metrics HTML."""
        if not results:
            return "<p>No results available</p>"
            
        avg_response_time = statistics.mean(r.average_response_time_ms for r in results)
        max_throughput = max(r.requests_per_second for r in results)
        avg_error_rate = statistics.mean(
            (r.failed_requests / r.total_requests * 100) if r.total_requests > 0 else 0
            for r in results
        )
        
        return f"""
        <div class="metric">
            <strong>Average Response Time:</strong><br>
            {avg_response_time:.2f} ms
        </div>
        <div class="metric">
            <strong>Peak Throughput:</strong><br>
            {max_throughput:.2f} req/sec
        </div>
        <div class="metric">
            <strong>Average Error Rate:</strong><br>
            {avg_error_rate:.2f}%
        </div>
        """
        
    def _generate_results_table(self, results: List[BenchmarkResult]) -> str:
        """Generate detailed results table HTML."""
        if not results:
            return "<p>No results available</p>"
            
        html = """
        <table>
            <tr>
                <th>Config</th>
                <th>Users</th>
                <th>Servers</th>
                <th>RPS</th>
                <th>Avg RT (ms)</th>
                <th>P95 RT (ms)</th>
                <th>Error Rate (%)</th>
                <th>Memory (MB)</th>
                <th>CPU (%)</th>
            </tr>
        """
        
        for result in results:
            error_rate = (
                (result.failed_requests / result.total_requests * 100)
                if result.total_requests > 0 else 0
            )
            
            html += f"""
            <tr>
                <td>{result.config_name}</td>
                <td>{result.concurrent_users}</td>
                <td>{result.server_count}</td>
                <td>{result.requests_per_second:.2f}</td>
                <td>{result.average_response_time_ms:.2f}</td>
                <td>{result.p95_response_time_ms:.2f}</td>
                <td>{error_rate:.2f}</td>
                <td>{result.peak_memory_usage_mb:.2f}</td>
                <td>{result.peak_cpu_usage_percent:.2f}</td>
            </tr>
            """
            
        html += "</table>"
        return html
        
    def _generate_recommendations(self, results: List[BenchmarkResult]) -> str:
        """Generate performance recommendations HTML."""
        recommendations = []
        
        if results:
            avg_response_time = statistics.mean(r.average_response_time_ms for r in results)
            max_error_rate = max(
                (r.failed_requests / r.total_requests * 100) if r.total_requests > 0 else 0
                for r in results
            )
            
            if avg_response_time > 5000:
                recommendations.append(
                    "Response times are high. Consider optimizing connection pools "
                    "or reducing timeout values."
                )
                
            if max_error_rate > 5:
                recommendations.append(
                    "Error rates are elevated. Check server capacity and "
                    "network connectivity."
                )
                
            # Add more recommendation logic based on results analysis
            
        if not recommendations:
            recommendations.append("Performance appears to be within acceptable limits.")
            
        html = "<ul>"
        for rec in recommendations:
            html += f"<li>{rec}</li>"
        html += "</ul>"
        
        return html


class MetricsCollector:
    """Collects system metrics during benchmarks."""
    
    def __init__(self):
        self.metrics_history = []
        self._collection_task: Optional[asyncio.Task] = None
        self._collecting = False
        
    async def start(self):
        """Start metrics collection."""
        self._collecting = True
        self._collection_task = asyncio.create_task(self._collect_metrics())
        
    async def stop(self):
        """Stop metrics collection."""
        self._collecting = False
        if self._collection_task:
            self._collection_task.cancel()
            
    async def get_final_metrics(self) -> Dict[str, float]:
        """Get aggregated final metrics."""
        if not self.metrics_history:
            return {
                'peak_memory_mb': 0,
                'avg_cpu_percent': 0,
                'peak_cpu_percent': 0,
                'pool_utilization': 0,
                'cache_hit_rate': 0
            }
            
        memory_values = [m['memory_mb'] for m in self.metrics_history]
        cpu_values = [m['cpu_percent'] for m in self.metrics_history]
        
        return {
            'peak_memory_mb': max(memory_values),
            'avg_cpu_percent': statistics.mean(cpu_values),
            'peak_cpu_percent': max(cpu_values),
            'pool_utilization': 0,  # Would be calculated from actual pool stats
            'cache_hit_rate': 0     # Would be calculated from actual cache stats
        }
        
    async def _collect_metrics(self):
        """Collect system metrics periodically."""
        import psutil
        
        while self._collecting:
            try:
                memory = psutil.virtual_memory()
                cpu_percent = psutil.cpu_percent(interval=0.1)
                
                self.metrics_history.append({
                    'timestamp': datetime.now(),
                    'memory_mb': memory.used / (1024 * 1024),
                    'cpu_percent': cpu_percent
                })
                
                await asyncio.sleep(1)  # Collect every second
                
            except asyncio.CancelledError:
                break
            except Exception:
                pass  # Ignore collection errors