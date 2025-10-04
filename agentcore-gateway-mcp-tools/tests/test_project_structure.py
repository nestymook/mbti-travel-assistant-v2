"""
Test project structure and basic configuration.

This test validates that all required files and directories are present
and properly configured for the AgentCore Gateway.
"""

import os
import json
import yaml
import pytest
from pathlib import Path


class TestProjectStructure:
    """Test the project structure and configuration files."""
    
    def test_required_files_exist(self):
        """Test that all required files exist."""
        required_files = [
            "main.py",
            "requirements.txt",
            "Dockerfile",
            ".bedrock_agentcore.yaml",
            "cognito_config.json",
            ".env.example",
            ".gitignore",
            ".dockerignore",
            "README.md"
        ]
        
        for file_path in required_files:
            assert os.path.exists(file_path), f"Required file {file_path} is missing"
    
    def test_required_directories_exist(self):
        """Test that all required directories exist."""
        required_dirs = [
            "models",
            "services", 
            "api",
            "middleware",
            "config",
            "tests",
            "scripts",
            "docs"
        ]
        
        for dir_path in required_dirs:
            assert os.path.isdir(dir_path), f"Required directory {dir_path} is missing"
            # Check that __init__.py exists in Python packages
            init_file = os.path.join(dir_path, "__init__.py")
            assert os.path.exists(init_file), f"Missing __init__.py in {dir_path}"
    
    def test_cognito_config_valid(self):
        """Test that Cognito configuration is valid."""
        with open("cognito_config.json", "r") as f:
            config = json.load(f)
        
        required_keys = [
            "user_pool_id",
            "client_id", 
            "region",
            "discovery_url",
            "jwks_uri",
            "issuer",
            "token_use",
            "bypass_paths"
        ]
        
        for key in required_keys:
            assert key in config, f"Missing required key {key} in cognito_config.json"
        
        # Validate specific values
        assert config["user_pool_id"] == "us-east-1_KePRX24Bn"
        assert config["client_id"] == "1ofgeckef3po4i3us4j1m4chvd"
        assert config["region"] == "us-east-1"
        assert isinstance(config["bypass_paths"], list)
    
    def test_agentcore_config_valid(self):
        """Test that AgentCore configuration is valid."""
        with open(".bedrock_agentcore.yaml", "r") as f:
            config = yaml.safe_load(f)
        
        # Test required top-level keys
        required_keys = [
            "name",
            "platform", 
            "container_runtime",
            "network_mode",
            "authentication",
            "observability",
            "environment"
        ]
        
        for key in required_keys:
            assert key in config, f"Missing required key {key} in .bedrock_agentcore.yaml"
        
        # Validate specific values
        assert config["name"] == "agentcore-gateway-mcp-tools"
        assert config["platform"] == "linux/arm64"
        assert config["container_runtime"] == "docker"
        
        # Validate authentication configuration
        auth_config = config["authentication"]
        assert auth_config["type"] == "jwt"
        assert "customJWTAuthorizer" in auth_config["config"]
        
        jwt_config = auth_config["config"]["customJWTAuthorizer"]
        assert "1ofgeckef3po4i3us4j1m4chvd" in jwt_config["allowedClients"]
        assert "us-east-1_KePRX24Bn" in jwt_config["discoveryUrl"]
    
    def test_dockerfile_arm64_platform(self):
        """Test that Dockerfile specifies ARM64 platform."""
        with open("Dockerfile", "r") as f:
            dockerfile_content = f.read()
        
        # Check for ARM64 platform specification
        assert "--platform=linux/arm64" in dockerfile_content, \
            "Dockerfile must specify --platform=linux/arm64 for AgentCore Runtime"
        
        # Check for required base image
        assert "FROM --platform=linux/arm64" in dockerfile_content, \
            "Dockerfile must use ARM64 base image"
        
        # Check for required ports
        assert "EXPOSE 8080" in dockerfile_content, \
            "Dockerfile must expose port 8080"
    
    def test_requirements_txt_dependencies(self):
        """Test that requirements.txt contains required dependencies."""
        with open("requirements.txt", "r") as f:
            requirements = f.read()
        
        required_packages = [
            "fastapi",
            "uvicorn",
            "pydantic",
            "PyJWT",
            "mcp",
            "boto3",
            "aws-opentelemetry-distro",
            "structlog",
            "httpx",
            "requests"
        ]
        
        for package in required_packages:
            assert package in requirements, f"Missing required package {package} in requirements.txt"
    
    def test_main_py_structure(self):
        """Test that main.py has the correct structure."""
        with open("main.py", "r") as f:
            main_content = f.read()
        
        # Check for required imports and components
        required_elements = [
            "from fastapi import FastAPI",
            "from fastapi.middleware.cors import CORSMiddleware",
            "import structlog",
            "app = FastAPI(",
            "@app.get(\"/health\")",
            "if __name__ == \"__main__\":"
        ]
        
        for element in required_elements:
            assert element in main_content, f"Missing required element {element} in main.py"
    
    def test_config_settings_structure(self):
        """Test that config/settings.py has the correct structure."""
        settings_file = "config/settings.py"
        assert os.path.exists(settings_file), "config/settings.py is missing"
        
        with open(settings_file, "r") as f:
            settings_content = f.read()
        
        # Check for required classes
        required_classes = [
            "class CognitoSettings",
            "class MCPServerSettings", 
            "class ApplicationSettings",
            "class Settings"
        ]
        
        for class_name in required_classes:
            assert class_name in settings_content, f"Missing {class_name} in config/settings.py"
    
    def test_deployment_script_exists(self):
        """Test that deployment script exists and is executable."""
        deploy_script = "scripts/deploy_agentcore.py"
        assert os.path.exists(deploy_script), "Deployment script is missing"
        
        with open(deploy_script, "r") as f:
            script_content = f.read()
        
        # Check for required components
        required_elements = [
            "class AgentCoreDeployer",
            "def validate_prerequisites",
            "def build_container",
            "def deploy_to_agentcore",
            "def test_deployment"
        ]
        
        for element in required_elements:
            assert element in script_content, f"Missing {element} in deployment script"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])