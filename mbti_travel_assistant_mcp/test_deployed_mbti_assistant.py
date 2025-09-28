#!/usr/bin/env python3
"""
Test Deployed MBTI Travel Assistant MCP

This script tests the deployed MBTI Travel Assistant on Amazon Bedrock AgentCore Runtime
to ensure it's working correctly with authentication and MCP orchestration.
"""

import json
import sys
import time
import getpass
from typing import Dict, Any, Optional

import boto3
from boto