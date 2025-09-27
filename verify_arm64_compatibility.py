#!/usr/bin/env python3
"""
Verify ARM64 Compatibility for AgentCore Runtime Deployment

This script verifies that the Docker configuration and base images
support the required linux/arm64 architecture for AgentCore Runtime.
"""

import subprocess
import re
import json


def check_dockerfile_arm64():
    """Check if Dockerfile specifies ARM64 platform."""
    print("🔍 Checking Dockerfile ARM64 Configuration")
    print("=" * 45)
    
    try:
        with open('Dockerfile', 'r') as f:
            dockerfile_content = f.read()
        
        # Check for ARM64 platform specification
        arm64_patterns = [
            r'--platform=linux/arm64',
            r'--platform linux/arm64',
            r'TARGETPLATFORM.*arm64'
        ]
        
        arm64_found = False
        for pattern in arm64_patterns:
            if re.search(pattern, dockerfile_content, re.IGNORECASE):
                arm64_found = True
                print(f"✅ Found ARM64 platform specification: {pattern}")
                break
        
        if not arm64_found:
            print("❌ ARM64 platform specification NOT found in Dockerfile")
            print("🔧 Required: FROM --platform=linux/arm64 [base-image]")
            return False
        
        # Extract base image
        from_match = re.search(r'FROM\s+(?:--platform=linux/arm64\s+)?([^\s]+)', dockerfile_content)
        if from_match:
            base_image = from_match.group(1)
            print(f"📋 Base Image: {base_image}")
            return True, base_image
        
        return arm64_found, None
        
    except FileNotFoundError:
        print("❌ Dockerfile not found")
        return False, None
    except Exception as e:
        print(f"❌ Error reading Dockerfile: {e}")
        return False, None


def verify_base_image_arm64_support(base_image):
    """Verify that the base image supports ARM64."""
    print(f"\n🧪 Verifying ARM64 Support for: {base_image}")
    print("=" * 50)
    
    # Common ARM64-compatible Python base images
    arm64_compatible_images = {
        'python': 'Official Python images support ARM64',
        'ghcr.io/astral-sh/uv': 'UV Python package manager supports ARM64',
        'ubuntu': 'Ubuntu base images support ARM64',
        'alpine': 'Alpine Linux supports ARM64',
        'debian': 'Debian base images support ARM64'
    }
    
    # Check if base image is known to support ARM64
    for image_prefix, description in arm64_compatible_images.items():
        if base_image.startswith(image_prefix):
            print(f"✅ {description}")
            return True
    
    print(f"⚠️ Unknown base image ARM64 compatibility: {base_image}")
    print("💡 Recommended ARM64-compatible alternatives:")
    print("   - python:3.12-slim")
    print("   - ghcr.io/astral-sh/uv:python3.12-bookworm-slim")
    print("   - python:3.12-alpine")
    
    return None


def test_docker_buildx_arm64():
    """Test if Docker Buildx can build ARM64 images."""
    print(f"\n🔨 Testing Docker Buildx ARM64 Capability")
    print("=" * 40)
    
    try:
        # Check if Docker Buildx is available
        result = subprocess.run(['docker', 'buildx', 'version'], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ Docker Buildx is available")
            
            # Check available platforms
            result = subprocess.run(['docker', 'buildx', 'ls'], 
                                  capture_output=True, text=True, timeout=10)
            
            if 'linux/arm64' in result.stdout:
                print("✅ Docker Buildx supports linux/arm64")
                return True
            else:
                print("⚠️ Docker Buildx may not support linux/arm64")
                print("💡 Enable multi-platform builds:")
                print("   docker buildx create --use --platform linux/amd64,linux/arm64")
                return False
        else:
            print("❌ Docker Buildx not available")
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ Docker command timed out")
        return False
    except FileNotFoundError:
        print("❌ Docker not found - install Docker Desktop")
        return False
    except Exception as e:
        print(f"❌ Error testing Docker: {e}")
        return False


def check_agentcore_yaml_platform():
    """Check AgentCore YAML configuration for ARM64."""
    print(f"\n📋 Checking AgentCore Configuration")
    print("=" * 35)
    
    try:
        import yaml
        
        with open('.bedrock_agentcore.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        # Check platform specification in agents
        agents = config.get('agents', {})
        
        for agent_name, agent_config in agents.items():
            platform = agent_config.get('platform', 'not specified')
            print(f"Agent '{agent_name}': platform = {platform}")
            
            if platform == 'linux/arm64':
                print(f"✅ {agent_name} correctly configured for ARM64")
            else:
                print(f"❌ {agent_name} not configured for ARM64")
                print(f"🔧 Required: platform: linux/arm64")
                return False
        
        return True
        
    except FileNotFoundError:
        print("⚠️ .bedrock_agentcore.yaml not found")
        return None
    except Exception as e:
        print(f"❌ Error reading AgentCore config: {e}")
        return False


def generate_arm64_dockerfile():
    """Generate a corrected ARM64 Dockerfile."""
    print(f"\n🔧 Generating ARM64-Compatible Dockerfile")
    print("=" * 40)
    
    arm64_dockerfile = '''# REQUIRED: ARM64 platform for Amazon Bedrock AgentCore Runtime
FROM --platform=linux/arm64 ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# Configure UV for container environment
ENV UV_SYSTEM_PYTHON=1 UV_COMPILE_BYTECODE=1

# Install dependencies
COPY requirements.txt requirements.txt
RUN uv pip install -r requirements.txt

# Install observability tools
RUN uv pip install aws-opentelemetry-distro>=0.10.1

# Set AWS region environment variables
ENV AWS_REGION=us-east-1
ENV AWS_DEFAULT_REGION=us-east-1
ENV DOCKER_CONTAINER=1

# Create non-root user for security
RUN useradd -m -u 1000 bedrock_agentcore
USER bedrock_agentcore

# Expose MCP server ports
EXPOSE 8080
EXPOSE 8000

# Copy application code
COPY . .

# Start MCP server with observability
CMD ["opentelemetry-instrument", "python", "-m", "restaurant_mcp_server"]
'''
    
    try:
        with open('Dockerfile.arm64', 'w') as f:
            f.write(arm64_dockerfile)
        
        print("✅ Generated Dockerfile.arm64 with correct ARM64 configuration")
        print("💡 Replace your current Dockerfile with this version")
        return True
        
    except Exception as e:
        print(f"❌ Error generating Dockerfile: {e}")
        return False


def main():
    """Main verification function."""
    print("🏗️ AgentCore Runtime ARM64 Compatibility Verification")
    print("=" * 55)
    print("Amazon Bedrock AgentCore Runtime REQUIRES linux/arm64 architecture")
    print("=" * 55)
    
    results = {}
    
    # Test 1: Check Dockerfile
    dockerfile_ok, base_image = check_dockerfile_arm64()
    results['dockerfile'] = dockerfile_ok
    
    # Test 2: Verify base image ARM64 support
    if base_image:
        base_image_ok = verify_base_image_arm64_support(base_image)
        results['base_image'] = base_image_ok
    
    # Test 3: Test Docker Buildx
    buildx_ok = test_docker_buildx_arm64()
    results['buildx'] = buildx_ok
    
    # Test 4: Check AgentCore YAML
    yaml_ok = check_agentcore_yaml_platform()
    results['agentcore_yaml'] = yaml_ok
    
    # Summary
    print(f"\n📊 ARM64 Compatibility Summary")
    print("=" * 35)
    
    all_good = True
    for test_name, result in results.items():
        if result is True:
            print(f"✅ {test_name}: PASS")
        elif result is False:
            print(f"❌ {test_name}: FAIL")
            all_good = False
        else:
            print(f"⚠️ {test_name}: UNKNOWN")
    
    if all_good:
        print(f"\n🎉 ARM64 Configuration: READY for AgentCore Runtime!")
        print("✅ All components properly configured for linux/arm64")
    else:
        print(f"\n⚠️ ARM64 Configuration: NEEDS ATTENTION")
        print("🔧 Fix the failed components before deployment")
        
        # Generate corrected Dockerfile
        generate_arm64_dockerfile()
    
    print(f"\n💡 Remember: AgentCore Runtime deployment uses AWS CodeBuild")
    print("   CodeBuild automatically handles ARM64 cross-compilation")
    print("   No local ARM64 Docker setup required for deployment")
    
    return all_good


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)