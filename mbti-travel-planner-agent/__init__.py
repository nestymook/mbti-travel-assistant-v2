"""
MBTI Travel Planner Agent

A BedrockAgentCore runtime service that receives HTTP requests from web servers
and uses the Amazon Nova Pro foundation model to make HTTP API calls to the agentcore-gateway-mcp-tools service.
The system processes HTTP payloads containing district and meal time parameters,
uses HTTP gateway integration, and employs the Nova Pro model to intelligently
coordinate restaurant search and sentiment analysis.

Version: 2.0.0 (HTTP Gateway Integration)
"""

__version__ = "2.0.0"
__author__ = "MBTI Travel Planner Team"
__description__ = "BedrockAgentCore runtime with HTTP gateway integration for intelligent restaurant recommendations"