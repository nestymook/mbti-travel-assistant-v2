"""
MBTI Travel Assistant MCP

A BedrockAgentCore runtime service that receives HTTP requests from web servers
and uses an internal LLM agent to orchestrate MCP client calls to existing MCP servers.
The system processes HTTP payloads containing district and meal time parameters,
authenticates via JWT tokens, and employs an embedded foundation model to intelligently
coordinate restaurant search and sentiment analysis.

Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "MBTI Travel Assistant Team"
__description__ = "BedrockAgentCore runtime for intelligent restaurant recommendations"