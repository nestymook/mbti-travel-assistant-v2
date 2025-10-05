"""
Troubleshooting Guide Interface

This module provides comprehensive troubleshooting guides for dual monitoring issues,
including common problems, diagnostic steps, and resolution procedures.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import json

from models.dual_health_models import DualHealthCheckResult, ServerStatus
from services.enhanced_health_check_service import EnhancedHealthCheckService


logger = logging.getLogger(__name__)


class TroubleshootingCategory(Enum):
    """Troubleshooting categories."""
    MCP_ISSUES = "mcp_issues"
    REST_ISSUES = "rest_issues"
    AUTHENTICATION = "authentication"
    NETWORK = "network"
    CONFIGURATION = "configuration"
    PERFORMANCE = "performance"
    GENERAL = "general"


@dataclass
class TroubleshootingStep:
    """Individual troubleshooting step."""
    step_number: int
    title: str
    description: str
    command: Optional[str] = None
    expected_result: Optional[str] = None
    troubleshooting_notes: Optional[str] = None


@dataclass
class TroubleshootingGuide:
    """Complete troubleshooting guide."""
    guide_id: str
    title: str
    category: TroubleshootingCategory
    description: str
    symptoms: List[str]
    common_causes: List[str]
    steps: List[TroubleshootingStep]
    related_guides: List[str]
    severity: str = "medium"


class TroubleshootingGuideInterface:
    """
    Troubleshooting Guide Interface for dual monitoring issues.
    
    Provides comprehensive troubleshooting guides, diagnostic tools,
    and step-by-step resolution procedures for common dual monitoring problems.
    """
    
    def __init__(self):
        """Initialize Troubleshooting Guide Interface."""
        self._guides: Dict[str, TroubleshootingGuide] = {}
        self._current_guide: Optional[str] = None
        self._current_step: int = 0
        
        # Initialize troubleshooting guides
        self._initialize_troubleshooting_guides()
    
    def _initialize_troubleshooting_guides(self):
        """Initialize comprehensive troubleshooting guides."""
        
        # MCP Connection Issues
        mcp_connection_guide = TroubleshootingGuide(
            guide_id="mcp_connection_failure",
            title="MCP Connection Failures",
            category=TroubleshootingCategory.MCP_ISSUES,
            description="Diagnose and resolve MCP tools/list request failures",
            symptoms=[
                "MCP health checks consistently failing",
                "Connection timeout errors",
                "JSON-RPC 2.0 protocol errors",
                "Tools/list requests returning empty responses"
            ],
            common_causes=[
                "MCP server not running or unreachable",
                "Incorrect MCP endpoint URL",
                "Network connectivity issues",
                "Authentication/authorization failures",
                "MCP server overloaded or unresponsive"
            ],
            steps=[
                TroubleshootingStep(
                    step_number=1,
                    title="Verify MCP Server Status",
                    description="Check if the MCP server is running and accessible",
                    command="curl -X POST {mcp_endpoint} -H 'Content-Type: application/json' -d '{\"jsonrpc\":\"2.0\",\"method\":\"tools/list\",\"id\":1}'",
                    expected_result="JSON-RPC 2.0 response with tools list",
                    troubleshooting_notes="If connection fails, check server logs and network connectivity"
                ),
                TroubleshootingStep(
                    step_number=2,
                    title="Validate MCP Endpoint Configuration",
                    description="Ensure MCP endpoint URL is correct and accessible",
                    command="ping {mcp_host}",
                    expected_result="Successful ping responses",
                    troubleshooting_notes="Check DNS resolution and firewall rules"
                ),
                TroubleshootingStep(
                    step_number=3,
                    title="Test Authentication",
                    description="Verify authentication headers and credentials",
                    command="Check JWT token validity and expiration",
                    expected_result="Valid authentication token",
                    troubleshooting_notes="Refresh tokens if expired, check token format"
                ),
                TroubleshootingStep(
                    step_number=4,
                    title="Check MCP Protocol Compliance",
                    description="Verify JSON-RPC 2.0 request/response format",
                    command="Validate JSON-RPC 2.0 message structure",
                    expected_result="Properly formatted JSON-RPC messages",
                    troubleshooting_notes="Check for required fields: jsonrpc, method, id"
                ),
                TroubleshootingStep(
                    step_number=5,
                    title="Review Server Logs",
                    description="Examine MCP server logs for error details",
                    command="tail -f {mcp_server_log_path}",
                    expected_result="No error messages during health checks",
                    troubleshooting_notes="Look for authentication, protocol, or resource errors"
                )
            ],
            related_guides=["authentication_issues", "network_connectivity"],
            severity="high"
        )
        
        # REST Health Check Issues
        rest_health_guide = TroubleshootingGuide(
            guide_id="rest_health_failure",
            title="REST Health Check Failures",
            category=TroubleshootingCategory.REST_ISSUES,
            description="Diagnose and resolve REST health endpoint failures",
            symptoms=[
                "REST health checks returning HTTP errors",
                "Health endpoint timeouts",
                "Invalid or empty health responses",
                "Intermittent REST failures"
            ],
            common_causes=[
                "Health endpoint not implemented or misconfigured",
                "HTTP server issues or overload",
                "Incorrect health endpoint path",
                "Authentication/authorization problems",
                "Network connectivity issues"
            ],
            steps=[
                TroubleshootingStep(
                    step_number=1,
                    title="Test Health Endpoint Directly",
                    description="Make direct HTTP request to health endpoint",
                    command="curl -v {rest_health_endpoint}",
                    expected_result="HTTP 200 response with health data",
                    troubleshooting_notes="Check HTTP status code and response body format"
                ),
                TroubleshootingStep(
                    step_number=2,
                    title="Verify Endpoint Path",
                    description="Confirm health endpoint path is correct",
                    command="Check server documentation for correct health endpoint path",
                    expected_result="Correct endpoint path configuration",
                    troubleshooting_notes="Common paths: /health, /status/health, /api/health"
                ),
                TroubleshootingStep(
                    step_number=3,
                    title="Check HTTP Authentication",
                    description="Verify HTTP authentication headers",
                    command="curl -H 'Authorization: Bearer {token}' {rest_health_endpoint}",
                    expected_result="Successful authentication",
                    troubleshooting_notes="Check token format, expiration, and permissions"
                ),
                TroubleshootingStep(
                    step_number=4,
                    title="Validate Response Format",
                    description="Ensure health response contains expected data",
                    command="Check response JSON structure and required fields",
                    expected_result="Valid health response with status indicators",
                    troubleshooting_notes="Look for status, timestamp, and metrics fields"
                ),
                TroubleshootingStep(
                    step_number=5,
                    title="Monitor Server Resources",
                    description="Check server CPU, memory, and network usage",
                    command="Monitor server performance metrics",
                    expected_result="Normal resource utilization",
                    troubleshooting_notes="High load may cause timeouts or slow responses"
                )
            ],
            related_guides=["authentication_issues", "performance_issues"],
            severity="high"
        )
        
        # Authentication Issues
        auth_issues_guide = TroubleshootingGuide(
            guide_id="authentication_issues",
            title="Authentication and Authorization Issues",
            category=TroubleshootingCategory.AUTHENTICATION,
            description="Resolve authentication failures in dual monitoring",
            symptoms=[
                "401 Unauthorized responses",
                "403 Forbidden errors",
                "JWT token validation failures",
                "Authentication timeouts"
            ],
            common_causes=[
                "Expired or invalid JWT tokens",
                "Incorrect authentication configuration",
                "Missing or malformed authorization headers",
                "Clock synchronization issues",
                "Insufficient permissions"
            ],
            steps=[
                TroubleshootingStep(
                    step_number=1,
                    title="Verify JWT Token",
                    description="Check JWT token validity and expiration",
                    command="Decode and validate JWT token",
                    expected_result="Valid, non-expired JWT token",
                    troubleshooting_notes="Use jwt.io or similar tools to decode token"
                ),
                TroubleshootingStep(
                    step_number=2,
                    title="Check Token Permissions",
                    description="Verify token has required scopes/permissions",
                    command="Review token claims and permissions",
                    expected_result="Token contains required scopes",
                    troubleshooting_notes="Check 'scope' or 'permissions' claims in token"
                ),
                TroubleshootingStep(
                    step_number=3,
                    title="Validate OIDC Configuration",
                    description="Ensure OIDC discovery URL and settings are correct",
                    command="curl {oidc_discovery_url}/.well-known/openid-configuration",
                    expected_result="Valid OIDC configuration response",
                    troubleshooting_notes="Check issuer, jwks_uri, and supported algorithms"
                ),
                TroubleshootingStep(
                    step_number=4,
                    title="Test Token Refresh",
                    description="Attempt to refresh expired tokens",
                    command="Use refresh token to obtain new access token",
                    expected_result="New valid access token",
                    troubleshooting_notes="Check refresh token validity and configuration"
                ),
                TroubleshootingStep(
                    step_number=5,
                    title="Verify Clock Synchronization",
                    description="Ensure system clocks are synchronized",
                    command="Check system time and NTP synchronization",
                    expected_result="Synchronized system time",
                    troubleshooting_notes="JWT tokens are time-sensitive (iat, exp claims)"
                )
            ],
            related_guides=["mcp_connection_failure", "rest_health_failure"],
            severity="critical"
        )
        
        # Network Connectivity Issues
        network_guide = TroubleshootingGuide(
            guide_id="network_connectivity",
            title="Network Connectivity Issues",
            category=TroubleshootingCategory.NETWORK,
            description="Diagnose and resolve network connectivity problems",
            symptoms=[
                "Connection timeouts",
                "DNS resolution failures",
                "Intermittent connectivity",
                "Slow response times"
            ],
            common_causes=[
                "Network infrastructure issues",
                "Firewall blocking connections",
                "DNS configuration problems",
                "Load balancer issues",
                "SSL/TLS certificate problems"
            ],
            steps=[
                TroubleshootingStep(
                    step_number=1,
                    title="Test Basic Connectivity",
                    description="Verify basic network connectivity to target hosts",
                    command="ping {target_host}",
                    expected_result="Successful ping responses",
                    troubleshooting_notes="Check for packet loss and high latency"
                ),
                TroubleshootingStep(
                    step_number=2,
                    title="Check DNS Resolution",
                    description="Verify DNS resolution for target hosts",
                    command="nslookup {target_host}",
                    expected_result="Correct IP address resolution",
                    troubleshooting_notes="Check DNS server configuration and cache"
                ),
                TroubleshootingStep(
                    step_number=3,
                    title="Test Port Connectivity",
                    description="Check if target ports are accessible",
                    command="telnet {target_host} {target_port}",
                    expected_result="Successful connection to target port",
                    troubleshooting_notes="Check firewall rules and port availability"
                ),
                TroubleshootingStep(
                    step_number=4,
                    title="Verify SSL/TLS Certificates",
                    description="Check SSL certificate validity for HTTPS endpoints",
                    command="openssl s_client -connect {target_host}:{port}",
                    expected_result="Valid SSL certificate chain",
                    troubleshooting_notes="Check certificate expiration and trust chain"
                ),
                TroubleshootingStep(
                    step_number=5,
                    title="Monitor Network Performance",
                    description="Check network latency and throughput",
                    command="traceroute {target_host}",
                    expected_result="Reasonable network path and latency",
                    troubleshooting_notes="Look for high latency hops or timeouts"
                )
            ],
            related_guides=["performance_issues"],
            severity="medium"
        )
        
        # Configuration Issues
        config_guide = TroubleshootingGuide(
            guide_id="configuration_issues",
            title="Configuration Problems",
            category=TroubleshootingCategory.CONFIGURATION,
            description="Resolve dual monitoring configuration issues",
            symptoms=[
                "Invalid configuration errors",
                "Missing required settings",
                "Incorrect endpoint URLs",
                "Mismatched authentication settings"
            ],
            common_causes=[
                "Syntax errors in configuration files",
                "Missing required configuration parameters",
                "Incorrect URL formats",
                "Mismatched authentication settings",
                "Invalid timeout or retry values"
            ],
            steps=[
                TroubleshootingStep(
                    step_number=1,
                    title="Validate Configuration Syntax",
                    description="Check configuration file syntax and structure",
                    command="Validate JSON/YAML configuration syntax",
                    expected_result="Valid configuration file format",
                    troubleshooting_notes="Use JSON/YAML validators to check syntax"
                ),
                TroubleshootingStep(
                    step_number=2,
                    title="Verify Required Settings",
                    description="Ensure all required configuration parameters are present",
                    command="Check for required configuration fields",
                    expected_result="All required settings configured",
                    troubleshooting_notes="Review configuration schema documentation"
                ),
                TroubleshootingStep(
                    step_number=3,
                    title="Test Configuration Loading",
                    description="Verify configuration loads without errors",
                    command="Test configuration loading process",
                    expected_result="Configuration loads successfully",
                    troubleshooting_notes="Check application logs for configuration errors"
                ),
                TroubleshootingStep(
                    step_number=4,
                    title="Validate URL Formats",
                    description="Check endpoint URL formats and accessibility",
                    command="Validate URL syntax and test accessibility",
                    expected_result="Valid, accessible endpoint URLs",
                    troubleshooting_notes="Ensure URLs include protocol (http/https)"
                ),
                TroubleshootingStep(
                    step_number=5,
                    title="Review Default Values",
                    description="Check if default values are appropriate",
                    command="Review timeout, retry, and other default settings",
                    expected_result="Appropriate default configuration values",
                    troubleshooting_notes="Adjust timeouts based on network conditions"
                )
            ],
            related_guides=["mcp_connection_failure", "rest_health_failure"],
            severity="medium"
        )
        
        # Performance Issues
        performance_guide = TroubleshootingGuide(
            guide_id="performance_issues",
            title="Performance and Timeout Issues",
            category=TroubleshootingCategory.PERFORMANCE,
            description="Resolve performance degradation and timeout problems",
            symptoms=[
                "Slow health check responses",
                "Frequent timeout errors",
                "High resource usage",
                "Degraded system performance"
            ],
            common_causes=[
                "Server overload or resource constraints",
                "Network latency issues",
                "Inefficient health check implementation",
                "Too many concurrent checks",
                "Insufficient timeout values"
            ],
            steps=[
                TroubleshootingStep(
                    step_number=1,
                    title="Monitor Response Times",
                    description="Measure and analyze health check response times",
                    command="Monitor health check latency metrics",
                    expected_result="Consistent, reasonable response times",
                    troubleshooting_notes="Look for patterns in slow responses"
                ),
                TroubleshootingStep(
                    step_number=2,
                    title="Check Server Resources",
                    description="Monitor CPU, memory, and network usage",
                    command="Monitor server resource utilization",
                    expected_result="Normal resource usage levels",
                    troubleshooting_notes="High CPU/memory may indicate overload"
                ),
                TroubleshootingStep(
                    step_number=3,
                    title="Optimize Concurrent Checks",
                    description="Adjust concurrent health check limits",
                    command="Review and adjust max_concurrent_checks setting",
                    expected_result="Balanced concurrency without overload",
                    troubleshooting_notes="Too many concurrent checks can overwhelm servers"
                ),
                TroubleshootingStep(
                    step_number=4,
                    title="Tune Timeout Values",
                    description="Adjust timeout settings based on performance",
                    command="Review and adjust timeout configurations",
                    expected_result="Appropriate timeout values for network conditions",
                    troubleshooting_notes="Balance between responsiveness and reliability"
                ),
                TroubleshootingStep(
                    step_number=5,
                    title="Implement Caching",
                    description="Enable result caching to reduce load",
                    command="Configure health check result caching",
                    expected_result="Reduced server load through caching",
                    troubleshooting_notes="Balance cache TTL with freshness requirements"
                )
            ],
            related_guides=["network_connectivity"],
            severity="medium"
        )
        
        # Store guides
        self._guides = {
            guide.guide_id: guide for guide in [
                mcp_connection_guide,
                rest_health_guide,
                auth_issues_guide,
                network_guide,
                config_guide,
                performance_guide
            ]
        }
    
    async def display_troubleshooting_menu(self):
        """Display main troubleshooting menu."""
        print("\n🔧 Troubleshooting Guide Menu")
        print("-" * 40)
        
        # Group guides by category
        categories = {}
        for guide in self._guides.values():
            category = guide.category.value
            if category not in categories:
                categories[category] = []
            categories[category].append(guide)
        
        # Display categories and guides
        guide_index = 1
        guide_map = {}
        
        for category, guides in categories.items():
            print(f"\n📂 {category.replace('_', ' ').title()}:")
            for guide in guides:
                severity_icon = self._get_severity_icon(guide.severity)
                print(f"  {guide_index}. {severity_icon} {guide.title}")
                guide_map[guide_index] = guide.guide_id
                guide_index += 1
        
        print(f"\n  {guide_index}. 🔍 Run Diagnostic Wizard")
        print(f"  {guide_index + 1}. 📊 System Health Summary")
        print(f"  {guide_index + 2}. ❓ Common Issues FAQ")
        
        print("\nSelect a troubleshooting guide or diagnostic tool:")
        return guide_map
    
    async def run_troubleshooting_guide(self, guide_id: str):
        """Run a specific troubleshooting guide."""
        guide = self._guides.get(guide_id)
        if not guide:
            print(f"❌ Guide not found: {guide_id}")
            return
        
        self._current_guide = guide_id
        self._current_step = 0
        
        print(f"\n🔧 {guide.title}")
        print("=" * (len(guide.title) + 4))
        
        print(f"\n📝 Description:")
        print(f"  {guide.description}")
        
        print(f"\n🔍 Symptoms:")
        for symptom in guide.symptoms:
            print(f"  • {symptom}")
        
        print(f"\n🎯 Common Causes:")
        for cause in guide.common_causes:
            print(f"  • {cause}")
        
        print(f"\n📋 Troubleshooting Steps ({len(guide.steps)} steps):")
        
        # Run through steps
        for i, step in enumerate(guide.steps, 1):
            await self._run_troubleshooting_step(step, i, len(guide.steps))
            
            if i < len(guide.steps):
                continue_step = await self._get_user_confirmation(
                    f"Continue to step {i + 1}?",
                    default=True
                )
                if not continue_step:
                    break
        
        print(f"\n✅ Troubleshooting guide completed!")
        
        # Show related guides
        if guide.related_guides:
            print(f"\n🔗 Related Guides:")
            for related_id in guide.related_guides:
                related_guide = self._guides.get(related_id)
                if related_guide:
                    print(f"  • {related_guide.title}")
    
    async def _run_troubleshooting_step(self, step: TroubleshootingStep, step_num: int, total_steps: int):
        """Run individual troubleshooting step."""
        print(f"\n📍 Step {step_num}/{total_steps}: {step.title}")
        print("-" * 50)
        
        print(f"Description: {step.description}")
        
        if step.command:
            print(f"\n💻 Command to run:")
            print(f"  {step.command}")
        
        if step.expected_result:
            print(f"\n✅ Expected result:")
            print(f"  {step.expected_result}")
        
        if step.troubleshooting_notes:
            print(f"\n💡 Troubleshooting notes:")
            print(f"  {step.troubleshooting_notes}")
        
        # Ask user about step result
        step_successful = await self._get_user_confirmation(
            "Was this step successful?",
            default=None
        )
        
        if step_successful:
            print("✅ Step completed successfully")
        else:
            print("❌ Step failed - review troubleshooting notes")
            
            # Offer additional help
            need_help = await self._get_user_confirmation(
                "Do you need additional help with this step?",
                default=False
            )
            
            if need_help:
                await self._provide_additional_help(step)
    
    async def _provide_additional_help(self, step: TroubleshootingStep):
        """Provide additional help for a troubleshooting step."""
        print(f"\n🆘 Additional Help for: {step.title}")
        print("-" * 40)
        
        # Provide step-specific additional guidance
        if "mcp" in step.title.lower():
            print("MCP-specific help:")
            print("• Check MCP server logs for detailed error messages")
            print("• Verify JSON-RPC 2.0 protocol compliance")
            print("• Test with a simple MCP client tool")
            print("• Check MCP server documentation for troubleshooting")
        
        elif "rest" in step.title.lower() or "http" in step.title.lower():
            print("REST/HTTP-specific help:")
            print("• Use browser or curl to test endpoint manually")
            print("• Check HTTP status codes and response headers")
            print("• Verify content-type and response format")
            print("• Review web server logs for errors")
        
        elif "auth" in step.title.lower():
            print("Authentication-specific help:")
            print("• Decode JWT tokens to check claims and expiration")
            print("• Verify OIDC provider configuration")
            print("• Check system time synchronization")
            print("• Test with fresh authentication tokens")
        
        elif "network" in step.title.lower():
            print("Network-specific help:")
            print("• Check firewall rules and port accessibility")
            print("• Verify DNS resolution and routing")
            print("• Test from different network locations")
            print("• Monitor network latency and packet loss")
        
        else:
            print("General troubleshooting tips:")
            print("• Check application and system logs")
            print("• Verify configuration settings")
            print("• Test with minimal configuration")
            print("• Contact support with detailed error information")
    
    async def run_diagnostic_wizard(self):
        """Run interactive diagnostic wizard."""
        print("\n🔍 Diagnostic Wizard")
        print("=" * 20)
        
        print("This wizard will help identify the most likely cause of your issue.")
        print("Please answer the following questions:")
        
        # Collect symptoms
        symptoms = await self._collect_symptoms()
        
        # Analyze symptoms and suggest guides
        suggested_guides = self._analyze_symptoms(symptoms)
        
        print(f"\n📊 Diagnostic Results:")
        print("-" * 25)
        
        if suggested_guides:
            print("Based on your symptoms, these guides may help:")
            for i, (guide_id, confidence) in enumerate(suggested_guides, 1):
                guide = self._guides[guide_id]
                confidence_bar = "█" * int(confidence * 10) + "░" * (10 - int(confidence * 10))
                print(f"  {i}. {guide.title}")
                print(f"     Confidence: {confidence_bar} {confidence:.0%}")
        else:
            print("No specific guides match your symptoms.")
            print("Try the general troubleshooting approach or contact support.")
        
        # Offer to run suggested guide
        if suggested_guides:
            run_guide = await self._get_user_confirmation(
                f"Run the top suggested guide ({self._guides[suggested_guides[0][0]].title})?",
                default=True
            )
            
            if run_guide:
                await self.run_troubleshooting_guide(suggested_guides[0][0])
    
    async def _collect_symptoms(self) -> Dict[str, bool]:
        """Collect symptoms from user."""
        symptoms = {}
        
        questions = [
            ("mcp_failing", "Are MCP health checks failing?"),
            ("rest_failing", "Are REST health checks failing?"),
            ("auth_errors", "Are you seeing authentication/authorization errors?"),
            ("timeout_errors", "Are you experiencing timeout errors?"),
            ("slow_responses", "Are health checks responding slowly?"),
            ("intermittent_issues", "Are the issues intermittent/occasional?"),
            ("recent_changes", "Have there been recent configuration changes?"),
            ("network_issues", "Are there known network connectivity issues?")
        ]
        
        for key, question in questions:
            answer = await self._get_user_confirmation(question, default=None)
            symptoms[key] = answer if answer is not None else False
        
        return symptoms
    
    def _analyze_symptoms(self, symptoms: Dict[str, bool]) -> List[Tuple[str, float]]:
        """Analyze symptoms and return suggested guides with confidence scores."""
        guide_scores = {}
        
        for guide_id, guide in self._guides.items():
            score = 0.0
            
            # Score based on symptom matching
            if symptoms.get("mcp_failing") and "mcp" in guide_id:
                score += 0.4
            
            if symptoms.get("rest_failing") and "rest" in guide_id:
                score += 0.4
            
            if symptoms.get("auth_errors") and "auth" in guide_id:
                score += 0.5
            
            if symptoms.get("timeout_errors") and guide.category == TroubleshootingCategory.NETWORK:
                score += 0.3
            
            if symptoms.get("slow_responses") and guide.category == TroubleshootingCategory.PERFORMANCE:
                score += 0.4
            
            if symptoms.get("recent_changes") and guide.category == TroubleshootingCategory.CONFIGURATION:
                score += 0.3
            
            if symptoms.get("network_issues") and guide.category == TroubleshootingCategory.NETWORK:
                score += 0.4
            
            # Boost score for high severity issues
            if guide.severity == "critical":
                score += 0.1
            elif guide.severity == "high":
                score += 0.05
            
            if score > 0:
                guide_scores[guide_id] = min(score, 1.0)
        
        # Sort by score and return top suggestions
        sorted_guides = sorted(guide_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_guides[:3]  # Top 3 suggestions
    
    async def display_system_health_summary(self):
        """Display system health summary for troubleshooting context."""
        print("\n📊 System Health Summary")
        print("-" * 30)
        
        # This would integrate with the health check service
        print("Current system status and recent issues will be displayed here.")
        print("This helps provide context for troubleshooting.")
        
        # Placeholder for actual health data
        print("\n🟢 Overall Status: HEALTHY")
        print("📈 Health Score: 0.95")
        print("🖥️  Monitored Servers: 3")
        print("⚡ Avg Response Time: 150ms")
        print("\n🚨 Recent Issues: None")
    
    async def display_common_issues_faq(self):
        """Display frequently asked questions about common issues."""
        print("\n❓ Common Issues FAQ")
        print("-" * 25)
        
        faqs = [
            {
                "question": "Why are my MCP health checks failing?",
                "answer": "Common causes include server downtime, network issues, authentication problems, or incorrect endpoint configuration. Run the MCP Connection Failures guide for detailed troubleshooting."
            },
            {
                "question": "What does 'DEGRADED' status mean?",
                "answer": "DEGRADED status indicates that one monitoring method (MCP or REST) is working while the other is failing. The service is partially functional but not fully healthy."
            },
            {
                "question": "How do I fix authentication errors?",
                "answer": "Check JWT token validity, expiration, and permissions. Verify OIDC configuration and ensure system clocks are synchronized. Use the Authentication Issues guide for detailed steps."
            },
            {
                "question": "Why are health checks timing out?",
                "answer": "Timeouts can be caused by network latency, server overload, or insufficient timeout values. Check network connectivity and consider increasing timeout settings."
            },
            {
                "question": "How can I improve health check performance?",
                "answer": "Optimize concurrent check limits, implement result caching, tune timeout values, and monitor server resources. See the Performance Issues guide for detailed optimization steps."
            }
        ]
        
        for i, faq in enumerate(faqs, 1):
            print(f"\n{i}. {faq['question']}")
            print(f"   {faq['answer']}")
    
    def _get_severity_icon(self, severity: str) -> str:
        """Get severity icon for display."""
        icons = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🔵"
        }
        return icons.get(severity, "⚪")
    
    async def _get_user_confirmation(self, prompt: str, default: Optional[bool] = None) -> Optional[bool]:
        """Get yes/no confirmation from user."""
        if default is True:
            prompt_suffix = " [Y/n]: "
        elif default is False:
            prompt_suffix = " [y/N]: "
        else:
            prompt_suffix = " [y/n]: "
        
        full_prompt = prompt + prompt_suffix
        
        loop = asyncio.get_event_loop()
        user_input = await loop.run_in_executor(None, input, full_prompt)
        
        if not user_input.strip():
            return default
        
        response = user_input.strip().lower()
        if response in ["y", "yes", "true", "1"]:
            return True
        elif response in ["n", "no", "false", "0"]:
            return False
        else:
            return default