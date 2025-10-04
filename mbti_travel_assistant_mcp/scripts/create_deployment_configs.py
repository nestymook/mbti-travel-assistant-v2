#!/usr/bin/env python3
"""
Environment-Specific Deployment Configuration Generator

This script generates environment-specific deployment configurations for the
MBTI Travel Assistant MCP, including AgentCore configurations, environment
variables, resource allocations, and monitoring settings.
"""

import json
import os
import sys
import logging
import yaml
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DeploymentConfigGenerator:
    """
    Generates environment-specific deployment configurations.
    
    Creates comprehensive configuration files for different environments
    including AgentCore settings, resource allocations, monitoring,
    and security configurations.
    """
    
    def __init__(self, base_config_dir: str = "config"):
        """
        Initialize deployment config generator.
        
        Args:
            base_config_dir: Base directory for configuration files
        """
        self.base_config_dir = Path(base_config_dir)
        self.environments_dir = self.base_config_dir / "environments"
        self.templates_dir = self.base_config_dir / "templates"
        
        # Ensure directories exist
        self.environments_dir.mkdir(parents=True, exist_ok=True)
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initialized deployment config generator with base dir: {self.base_config_dir}")
    
    def generate_all_environment_configs(
        self,
        agent_name: str = "mbti-travel-assistant-mcp",
        region: str = "us-east-1",
        account_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate configurations for all environments.
        
        Args:
            agent_name: Name of the agent
            region: AWS region
            account_id: AWS account ID (optional)
            
        Returns:
            Dictionary with generation results
        """
        logger.info("Generating configurations for all environments")
        
        environments = ["development", "staging", "production"]
        generation_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "agent_name": agent_name,
            "region": region,
            "account_id": account_id,
            "environments": {}
        }
        
        for environment in environments:
            try:
                logger.info(f"Generating configuration for {environment}")
                
                env_result = self.generate_environment_config(
                    environment=environment,
                    agent_name=agent_name,
                    region=region,
                    account_id=account_id
                )
                
                generation_results["environments"][environment] = env_result
                
            except Exception as e:
                logger.error(f"Failed to generate config for {environment}: {e}")
                generation_results["environments"][environment] = {
                    "success": False,
                    "error": str(e)
                }
        
        # Generate summary
        successful_envs = [env for env, result in generation_results["environments"].items() 
                          if result.get("success", False)]
        
        generation_results["summary"] = {
            "total_environments": len(environments),
            "successful_environments": len(successful_envs),
            "failed_environments": len(environments) - len(successful_envs),
            "success_rate": len(successful_envs) / len(environments) * 100
        }
        
        logger.info(f"Configuration generation completed. Success rate: {generation_results['summary']['success_rate']:.1f}%")
        return generation_results
    
    def generate_environment_config(
        self,
        environment: str,
        agent_name: str = "mbti-travel-assistant-mcp",
        region: str = "us-east-1",
        account_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate configuration for a specific environment.
        
        Args:
            environment: Environment name (development, staging, production)
            agent_name: Name of the agent
            region: AWS region
            account_id: AWS account ID (optional)
            
        Returns:
            Generation result dictionary
        """
        logger.info(f"Generating configuration for environment: {environment}")
        
        result = {
            "environment": environment,
            "success": True,
            "generated_files": [],
            "errors": []
        }
        
        try:
            # 1. Generate environment variables file
            env_file = self._generate_environment_variables(environment, agent_name, region)
            result["generated_files"].append(env_file)
            
            # 2. Generate AgentCore configuration
            agentcore_config = self._generate_agentcore_config(environment, agent_name, region, account_id)
            result["generated_files"].append(agentcore_config)
            
            # 3. Generate Docker Compose configuration
            docker_compose_config = self._generate_docker_compose_config(environment, agent_name)
            result["generated_files"].append(docker_compose_config)
            
            # 4. Generate monitoring configuration
            monitoring_config = self._generate_monitoring_config(environment, agent_name, region)
            result["generated_files"].append(monitoring_config)
            
            # 5. Generate security configuration
            security_config = self._generate_security_config(environment, agent_name)
            result["generated_files"].append(security_config)
            
            # 6. Generate deployment script
            deployment_script = self._generate_deployment_script(environment, agent_name, region)
            result["generated_files"].append(deployment_script)
            
            # 7. Generate validation configuration
            validation_config = self._generate_validation_config(environment, agent_name)
            result["generated_files"].append(validation_config)
            
        except Exception as e:
            logger.error(f"Failed to generate configuration for {environment}: {e}")
            result["success"] = False
            result["errors"].append(str(e))
        
        return result
    
    def _generate_environment_variables(self, environment: str, agent_name: str, region: str) -> str:
        """Generate environment variables file."""
        env_config = self._get_environment_specific_config(environment)
        
        env_content = f"""# {environment.title()} Environment Configuration
# MBTI Travel Assistant MCP - {environment.title()} Settings

# Application Environment
ENVIRONMENT={environment}
AWS_REGION={region}
AWS_DEFAULT_REGION={region}

# MCP Client Configuration
SEARCH_MCP_ENDPOINT={env_config['mcp_endpoints']['search']}
REASONING_MCP_ENDPOINT={env_config['mcp_endpoints']['reasoning']}
MCP_CONNECTION_TIMEOUT={env_config['mcp_settings']['connection_timeout']}
MCP_RETRY_ATTEMPTS={env_config['mcp_settings']['retry_attempts']}

# Authentication Configuration
COGNITO_USER_POOL_ID={env_config['cognito']['user_pool_id_placeholder']}
COGNITO_REGION={region}
JWT_ALGORITHM=RS256
JWT_AUDIENCE={agent_name}-{environment}
TOKEN_CACHE_TTL={env_config['auth']['token_cache_ttl']}

# Cache Configuration
CACHE_ENABLED={str(env_config['cache']['enabled']).lower()}
CACHE_TTL={env_config['cache']['ttl']}
{f"REDIS_URL={env_config['cache']['redis_url']}" if env_config['cache'].get('redis_url') else "# REDIS_URL=redis://localhost:6379"}

# AgentCore Runtime Configuration
RUNTIME_PORT=8080
AGENT_MODEL={env_config['agent']['model']}
AGENT_TEMPERATURE={env_config['agent']['temperature']}
AGENT_MAX_TOKENS={env_config['agent']['max_tokens']}

# Logging Configuration
LOG_LEVEL={env_config['logging']['level']}
LOG_FORMAT={env_config['logging']['format']}
TRACING_ENABLED={str(env_config['observability']['tracing']).lower()}
METRICS_ENABLED={str(env_config['observability']['metrics']).lower()}

# Knowledge Base Configuration
KNOWLEDGE_BASE_ID=RCWW86CLM9
KNOWLEDGE_BASE_REGION={region}
KNOWLEDGE_BASE_MODEL={env_config['knowledge_base']['model']}
KB_MAX_RESULTS={env_config['knowledge_base']['max_results']}
KB_SEARCH_TYPE={env_config['knowledge_base']['search_type']}
KB_TEMPERATURE={env_config['knowledge_base']['temperature']}
KB_MAX_TOKENS={env_config['knowledge_base']['max_tokens']}

# Environment-specific settings
DEBUG={str(env_config['debug']).lower()}
MOCK_MCP_SERVERS={str(env_config['mock_mcp_servers']).lower()}

# Performance Configuration
MAX_CONCURRENT_REQUESTS={env_config['performance']['max_concurrent_requests']}
REQUEST_TIMEOUT={env_config['performance']['request_timeout']}
CIRCUIT_BREAKER_ENABLED={str(env_config['performance']['circuit_breaker_enabled']).lower()}

# Security Configuration
RATE_LIMITING_ENABLED={str(env_config['security']['rate_limiting_enabled']).lower()}
MAX_REQUESTS_PER_MINUTE={env_config['security']['max_requests_per_minute']}
SECURITY_HEADERS_ENABLED={str(env_config['security']['security_headers_enabled']).lower()}
"""
        
        env_file_path = self.environments_dir / f"{environment}.env"
        with open(env_file_path, 'w') as f:
            f.write(env_content)
        
        logger.info(f"Generated environment variables file: {env_file_path}")
        return str(env_file_path)
    
    def _generate_agentcore_config(self, environment: str, agent_name: str, region: str, account_id: Optional[str]) -> str:
        """Generate AgentCore configuration file."""
        env_config = self._get_environment_specific_config(environment)
        
        # Generate container URI
        container_uri = f"{account_id}.dkr.ecr.{region}.amazonaws.com/{agent_name.lower()}:latest" if account_id else f"<account-id>.dkr.ecr.{region}.amazonaws.com/{agent_name.lower()}:latest"
        
        agentcore_config = {
            "name": f"{agent_name}-{environment}",
            "container_uri": container_uri,
            "platform": "linux/arm64",
            "network_mode": env_config['network']['mode'],
            "authentication": {
                "type": "jwt",
                "config": {
                    "customJWTAuthorizer": {
                        "allowedClients": [f"<cognito-client-id-{environment}>"],
                        "discoveryUrl": f"https://cognito-idp.{region}.amazonaws.com/<user-pool-id>/.well-known/openid-configuration"
                    }
                }
            },
            "environment": {
                "AWS_REGION": region,
                "AWS_DEFAULT_REGION": region,
                "ENVIRONMENT": environment,
                "DOCKER_CONTAINER": "1"
            },
            "observability": {
                "enabled": env_config['observability']['enabled'],
                "tracing": env_config['observability']['tracing'],
                "metrics": env_config['observability']['metrics'],
                "logs": env_config['observability']['logs']
            },
            "resources": env_config['resources'],
            "scaling": env_config['scaling'],
            "health_check": {
                "path": "/health",
                "interval": env_config['health_check']['interval'],
                "timeout": env_config['health_check']['timeout'],
                "retries": env_config['health_check']['retries']
            },
            "security": {
                "vpc_config": env_config['security'].get('vpc_config'),
                "security_groups": env_config['security'].get('security_groups', []),
                "subnets": env_config['security'].get('subnets', [])
            }
        }
        
        config_file_path = self.base_config_dir / f"agentcore_{environment}.json"
        with open(config_file_path, 'w') as f:
            json.dump(agentcore_config, f, indent=2)
        
        logger.info(f"Generated AgentCore configuration: {config_file_path}")
        return str(config_file_path)
    
    def _generate_docker_compose_config(self, environment: str, agent_name: str) -> str:
        """Generate Docker Compose configuration."""
        env_config = self._get_environment_specific_config(environment)
        
        docker_compose = {
            "version": "3.8",
            "services": {
                agent_name.replace('-', '_'): {
                    "build": {
                        "context": ".",
                        "dockerfile": "Dockerfile",
                        "platform": "linux/arm64",
                        "args": {
                            "ENVIRONMENT": environment
                        }
                    },
                    "container_name": f"{agent_name}-{environment}",
                    "ports": [
                        f"{env_config['ports']['http']}:8080",
                        f"{env_config['ports']['metrics']}:9090"
                    ],
                    "environment": [
                        f"ENVIRONMENT={environment}",
                        "AWS_REGION=${AWS_REGION:-us-east-1}",
                        "DOCKER_CONTAINER=1"
                    ],
                    "env_file": [
                        f"config/environments/{environment}.env"
                    ],
                    "volumes": [
                        "./logs:/app/logs",
                        "./config:/app/config:ro"
                    ],
                    "restart": env_config['docker']['restart_policy'],
                    "healthcheck": {
                        "test": ["CMD", "curl", "-f", "http://localhost:8080/health"],
                        "interval": f"{env_config['health_check']['interval']}s",
                        "timeout": f"{env_config['health_check']['timeout']}s",
                        "retries": env_config['health_check']['retries'],
                        "start_period": "30s"
                    },
                    "deploy": {
                        "resources": {
                            "limits": {
                                "cpus": env_config['docker']['cpu_limit'],
                                "memory": env_config['docker']['memory_limit']
                            },
                            "reservations": {
                                "cpus": env_config['docker']['cpu_reservation'],
                                "memory": env_config['docker']['memory_reservation']
                            }
                        }
                    },
                    "logging": {
                        "driver": "json-file",
                        "options": {
                            "max-size": env_config['logging']['max_size'],
                            "max-file": str(env_config['logging']['max_files'])
                        }
                    }
                }
            },
            "networks": {
                "mbti_network": {
                    "driver": "bridge"
                }
            },
            "volumes": {
                "logs": {},
                "config": {}
            }
        }
        
        # Add monitoring services for non-development environments
        if environment != "development":
            docker_compose["services"]["prometheus"] = {
                "image": "prom/prometheus:latest",
                "container_name": f"prometheus-{environment}",
                "ports": ["9090:9090"],
                "volumes": [
                    f"./monitoring/prometheus.{environment}.yml:/etc/prometheus/prometheus.yml:ro",
                    "./monitoring/rules:/etc/prometheus/rules:ro"
                ],
                "command": [
                    "--config.file=/etc/prometheus/prometheus.yml",
                    "--storage.tsdb.path=/prometheus",
                    "--web.console.libraries=/etc/prometheus/console_libraries",
                    "--web.console.templates=/etc/prometheus/consoles",
                    f"--storage.tsdb.retention.time={env_config['monitoring']['retention_days']}d",
                    "--web.enable-lifecycle"
                ],
                "restart": "unless-stopped"
            }
            
            docker_compose["services"]["grafana"] = {
                "image": "grafana/grafana:latest",
                "container_name": f"grafana-{environment}",
                "ports": ["3000:3000"],
                "environment": [
                    "GF_SECURITY_ADMIN_PASSWORD=admin123",
                    "GF_INSTALL_PLUGINS=grafana-clock-panel,grafana-simple-json-datasource"
                ],
                "volumes": [
                    "grafana-storage:/var/lib/grafana",
                    f"./monitoring/grafana_dashboard_{environment}.json:/etc/grafana/provisioning/dashboards/dashboard.json:ro"
                ],
                "restart": "unless-stopped"
            }
            
            docker_compose["volumes"]["grafana-storage"] = {}
        
        compose_file_path = Path(f"docker-compose.{environment}.yml")
        with open(compose_file_path, 'w') as f:
            yaml.dump(docker_compose, f, default_flow_style=False, indent=2)
        
        logger.info(f"Generated Docker Compose configuration: {compose_file_path}")
        return str(compose_file_path)
    
    def _generate_monitoring_config(self, environment: str, agent_name: str, region: str) -> str:
        """Generate monitoring configuration."""
        env_config = self._get_environment_specific_config(environment)
        
        monitoring_config = {
            "environment": environment,
            "agent_name": agent_name,
            "region": region,
            "cloudwatch": {
                "namespace": "MBTI/TravelAssistant",
                "log_groups": [
                    f"/aws/lambda/{agent_name}-{environment}",
                    f"/mbti/travel-assistant/{environment}/application",
                    f"/mbti/travel-assistant/{environment}/mcp-calls",
                    f"/mbti/travel-assistant/{environment}/security"
                ],
                "retention_days": env_config['logging']['retention_days'],
                "metrics": {
                    "enabled": env_config['observability']['metrics'],
                    "custom_metrics": [
                        "RequestCount",
                        "ResponseTime",
                        "ErrorRate",
                        "MCPCallDuration",
                        "CacheHitRate",
                        "AuthenticationAttempts"
                    ]
                },
                "alarms": {
                    "high_error_rate": {
                        "threshold": env_config['alarms']['error_rate_threshold'],
                        "evaluation_periods": 2,
                        "period": 300
                    },
                    "high_response_time": {
                        "threshold": env_config['alarms']['response_time_threshold'],
                        "evaluation_periods": 2,
                        "period": 300
                    },
                    "low_throughput": {
                        "threshold": env_config['alarms']['throughput_threshold'],
                        "evaluation_periods": 3,
                        "period": 300
                    }
                }
            },
            "prometheus": {
                "enabled": environment != "development",
                "scrape_interval": "15s",
                "evaluation_interval": "15s",
                "retention": f"{env_config['monitoring']['retention_days']}d",
                "targets": [
                    f"{agent_name}:9090",
                    f"{agent_name}:8080"
                ]
            },
            "grafana": {
                "enabled": environment != "development",
                "dashboards": [
                    "application_metrics",
                    "mcp_performance",
                    "system_resources",
                    "security_events"
                ]
            },
            "health_checks": {
                "enabled": True,
                "interval": env_config['health_check']['interval'],
                "timeout": env_config['health_check']['timeout'],
                "endpoints": [
                    "/health",
                    "/health/ready",
                    "/health/live"
                ]
            }
        }
        
        monitoring_file_path = self.base_config_dir / f"monitoring_{environment}.json"
        with open(monitoring_file_path, 'w') as f:
            json.dump(monitoring_config, f, indent=2)
        
        logger.info(f"Generated monitoring configuration: {monitoring_file_path}")
        return str(monitoring_file_path)
    
    def _generate_security_config(self, environment: str, agent_name: str) -> str:
        """Generate security configuration."""
        env_config = self._get_environment_specific_config(environment)
        
        security_config = {
            "environment": environment,
            "agent_name": agent_name,
            "authentication": {
                "jwt": {
                    "algorithm": "RS256",
                    "audience": f"{agent_name}-{environment}",
                    "issuer_validation": True,
                    "token_cache_ttl": env_config['auth']['token_cache_ttl']
                },
                "rate_limiting": {
                    "enabled": env_config['security']['rate_limiting_enabled'],
                    "max_requests_per_minute": env_config['security']['max_requests_per_minute'],
                    "burst_limit": env_config['security']['burst_limit']
                }
            },
            "network_security": {
                "cors": {
                    "enabled": True,
                    "allowed_origins": env_config['security']['cors']['allowed_origins'],
                    "allowed_methods": ["GET", "POST", "OPTIONS"],
                    "allowed_headers": ["Content-Type", "Authorization"],
                    "max_age": 3600
                },
                "security_headers": {
                    "enabled": env_config['security']['security_headers_enabled'],
                    "headers": {
                        "X-Content-Type-Options": "nosniff",
                        "X-Frame-Options": "DENY",
                        "X-XSS-Protection": "1; mode=block",
                        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
                        "Content-Security-Policy": "default-src 'self'"
                    }
                }
            },
            "data_protection": {
                "encryption": {
                    "at_rest": True,
                    "in_transit": True,
                    "key_rotation": environment == "production"
                },
                "pii_handling": {
                    "logging_sanitization": True,
                    "data_masking": True,
                    "retention_policy": env_config['security']['data_retention_days']
                }
            },
            "audit_logging": {
                "enabled": True,
                "events": [
                    "authentication_attempts",
                    "authorization_failures",
                    "data_access",
                    "configuration_changes",
                    "security_violations"
                ],
                "retention_days": env_config['security']['audit_retention_days']
            },
            "vulnerability_management": {
                "container_scanning": environment == "production",
                "dependency_scanning": True,
                "security_updates": {
                    "automatic": environment != "production",
                    "notification": True
                }
            }
        }
        
        security_file_path = self.base_config_dir / f"security_{environment}.json"
        with open(security_file_path, 'w') as f:
            json.dump(security_config, f, indent=2)
        
        logger.info(f"Generated security configuration: {security_file_path}")
        return str(security_file_path)
    
    def _generate_deployment_script(self, environment: str, agent_name: str, region: str) -> str:
        """Generate deployment script for the environment."""
        script_content = f"""#!/bin/bash
# Deployment script for {agent_name} - {environment.title()} Environment
# Generated on {datetime.utcnow().isoformat()}

set -e

# Configuration
ENVIRONMENT="{environment}"
AGENT_NAME="{agent_name}"
REGION="{region}"
SCRIPT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🚀 Starting deployment for $AGENT_NAME in $ENVIRONMENT environment"
echo "Region: $REGION"
echo "Project Root: $PROJECT_ROOT"

# Load environment variables
if [ -f "$PROJECT_ROOT/config/environments/$ENVIRONMENT.env" ]; then
    echo "Loading environment variables from $ENVIRONMENT.env"
    set -a
    source "$PROJECT_ROOT/config/environments/$ENVIRONMENT.env"
    set +a
else
    echo "❌ Environment file not found: $PROJECT_ROOT/config/environments/$ENVIRONMENT.env"
    exit 1
fi

# Function to check prerequisites
check_prerequisites() {{
    echo "🔍 Checking prerequisites..."
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        echo "❌ AWS CLI not found. Please install AWS CLI."
        exit 1
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker not found. Please install Docker."
        exit 1
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python 3 not found. Please install Python 3."
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        echo "❌ AWS credentials not configured. Please run 'aws configure'."
        exit 1
    fi
    
    echo "✅ Prerequisites check passed"
}}

# Function to validate configuration
validate_configuration() {{
    echo "🔍 Validating configuration..."
    
    # Validate required files
    required_files=(
        "$PROJECT_ROOT/main.py"
        "$PROJECT_ROOT/requirements.txt"
        "$PROJECT_ROOT/Dockerfile"
        "$PROJECT_ROOT/.bedrock_agentcore.yaml"
        "$PROJECT_ROOT/config/environments/$ENVIRONMENT.env"
    )
    
    for file in "${{required_files[@]}}"; do
        if [ ! -f "$file" ]; then
            echo "❌ Required file not found: $file"
            exit 1
        fi
    done
    
    echo "✅ Configuration validation passed"
}}

# Function to build and push container
build_and_push_container() {{
    echo "🏗️ Building and pushing container..."
    
    # Get AWS account ID
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    
    # ECR repository URI
    ECR_URI="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/${{AGENT_NAME,,}}"
    
    # Login to ECR
    aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_URI
    
    # Build ARM64 container
    docker build --platform linux/arm64 \\
        --build-arg ENVIRONMENT=$ENVIRONMENT \\
        --build-arg AWS_REGION=$REGION \\
        -t $ECR_URI:$ENVIRONMENT-$(date +%s) \\
        -t $ECR_URI:latest \\
        $PROJECT_ROOT
    
    # Push container
    docker push $ECR_URI:$ENVIRONMENT-$(date +%s)
    docker push $ECR_URI:latest
    
    echo "✅ Container build and push completed"
    echo "Container URI: $ECR_URI:latest"
}}

# Function to deploy to AgentCore
deploy_to_agentcore() {{
    echo "🚀 Deploying to AgentCore..."
    
    # Run enhanced deployment script
    python3 "$PROJECT_ROOT/scripts/deploy_agentcore_enhanced.py" \\
        --environment $ENVIRONMENT \\
        --region $REGION \\
        --agent-name $AGENT_NAME
    
    echo "✅ AgentCore deployment completed"
}}

# Function to verify deployment
verify_deployment() {{
    echo "🔍 Verifying deployment..."
    
    # Run deployment verification
    python3 "$PROJECT_ROOT/scripts/validate_deployment.py" \\
        --environment $ENVIRONMENT \\
        --agent-name $AGENT_NAME
    
    echo "✅ Deployment verification completed"
}}

# Function to setup monitoring
setup_monitoring() {{
    echo "📊 Setting up monitoring..."
    
    # Run monitoring setup
    python3 "$PROJECT_ROOT/scripts/setup_monitoring.py" \\
        --environment $ENVIRONMENT \\
        --agent-name $AGENT_NAME \\
        --region $REGION
    
    echo "✅ Monitoring setup completed"
}}

# Main deployment flow
main() {{
    echo "Starting deployment process..."
    
    check_prerequisites
    validate_configuration
    
    # Build and push container (skip for development if requested)
    if [ "$ENVIRONMENT" != "development" ] || [ "${{SKIP_CONTAINER_BUILD:-false}}" != "true" ]; then
        build_and_push_container
    else
        echo "⏭️ Skipping container build for development environment"
    fi
    
    deploy_to_agentcore
    verify_deployment
    setup_monitoring
    
    echo ""
    echo "🎉 Deployment completed successfully!"
    echo "Environment: $ENVIRONMENT"
    echo "Agent: $AGENT_NAME"
    echo "Region: $REGION"
    echo ""
    echo "Next steps:"
    echo "1. Check CloudWatch logs for any issues"
    echo "2. Test the deployed agent"
    echo "3. Monitor performance metrics"
}}

# Handle script arguments
case "${{1:-}}" in
    "prerequisites")
        check_prerequisites
        ;;
    "validate")
        validate_configuration
        ;;
    "build")
        build_and_push_container
        ;;
    "deploy")
        deploy_to_agentcore
        ;;
    "verify")
        verify_deployment
        ;;
    "monitor")
        setup_monitoring
        ;;
    *)
        main
        ;;
esac
"""
        
        script_file_path = Path(f"scripts/deploy_{environment}.sh")
        script_file_path.parent.mkdir(exist_ok=True)
        
        with open(script_file_path, 'w') as f:
            f.write(script_content)
        
        # Make script executable
        os.chmod(script_file_path, 0o755)
        
        logger.info(f"Generated deployment script: {script_file_path}")
        return str(script_file_path)
    
    def _generate_validation_config(self, environment: str, agent_name: str) -> str:
        """Generate validation configuration."""
        env_config = self._get_environment_specific_config(environment)
        
        validation_config = {
            "environment": environment,
            "agent_name": agent_name,
            "validation_rules": {
                "response_time": {
                    "max_response_time_ms": env_config['validation']['max_response_time_ms'],
                    "percentile_threshold": 95
                },
                "error_rate": {
                    "max_error_rate": env_config['validation']['max_error_rate'],
                    "measurement_period_minutes": 5
                },
                "availability": {
                    "min_uptime_percentage": env_config['validation']['min_uptime_percentage'],
                    "measurement_period_hours": 24
                },
                "functionality": {
                    "required_endpoints": [
                        "/health",
                        "/health/ready",
                        "/health/live"
                    ],
                    "test_queries": [
                        "What tourist spots are suitable for INFJ personality?",
                        "Find restaurants for lunch in Central district",
                        "Show me outdoor activities in Hong Kong"
                    ]
                }
            },
            "test_scenarios": {
                "load_testing": {
                    "enabled": environment != "development",
                    "concurrent_users": env_config['testing']['concurrent_users'],
                    "duration_minutes": env_config['testing']['duration_minutes'],
                    "ramp_up_time_seconds": env_config['testing']['ramp_up_time_seconds']
                },
                "stress_testing": {
                    "enabled": environment == "production",
                    "max_concurrent_users": env_config['testing']['max_concurrent_users'],
                    "duration_minutes": env_config['testing']['stress_duration_minutes']
                },
                "security_testing": {
                    "enabled": True,
                    "authentication_tests": True,
                    "authorization_tests": True,
                    "input_validation_tests": True
                }
            },
            "monitoring_during_validation": {
                "metrics_to_monitor": [
                    "cpu_usage",
                    "memory_usage",
                    "response_time",
                    "error_rate",
                    "throughput"
                ],
                "alert_thresholds": env_config['validation']['alert_thresholds']
            }
        }
        
        validation_file_path = self.base_config_dir / f"validation_{environment}.json"
        with open(validation_file_path, 'w') as f:
            json.dump(validation_config, f, indent=2)
        
        logger.info(f"Generated validation configuration: {validation_file_path}")
        return str(validation_file_path)
    
    def _get_environment_specific_config(self, environment: str) -> Dict[str, Any]:
        """Get environment-specific configuration values."""
        configs = {
            "development": {
                "mcp_endpoints": {
                    "search": "http://localhost:8001",
                    "reasoning": "http://localhost:8002"
                },
                "mcp_settings": {
                    "connection_timeout": 30,
                    "retry_attempts": 3
                },
                "cognito": {
                    "user_pool_id_placeholder": "us-east-1_dev123456"
                },
                "auth": {
                    "token_cache_ttl": 300
                },
                "cache": {
                    "enabled": True,
                    "ttl": 300
                },
                "agent": {
                    "model": "amazon.nova-pro-v1:0:300k",
                    "temperature": 0.1,
                    "max_tokens": 4096
                },
                "logging": {
                    "level": "DEBUG",
                    "format": "text",
                    "retention_days": 7,
                    "max_size": "10m",
                    "max_files": 3
                },
                "observability": {
                    "enabled": True,
                    "tracing": True,
                    "metrics": True,
                    "logs": True
                },
                "knowledge_base": {
                    "model": "amazon.nova-pro-v1:0",
                    "max_results": 20,
                    "search_type": "HYBRID",
                    "temperature": 0.1,
                    "max_tokens": 4096
                },
                "debug": True,
                "mock_mcp_servers": True,
                "performance": {
                    "max_concurrent_requests": 10,
                    "request_timeout": 30,
                    "circuit_breaker_enabled": False
                },
                "security": {
                    "rate_limiting_enabled": False,
                    "max_requests_per_minute": 100,
                    "burst_limit": 20,
                    "security_headers_enabled": False,
                    "cors": {
                        "allowed_origins": ["*"]
                    },
                    "data_retention_days": 30,
                    "audit_retention_days": 90
                },
                "network": {
                    "mode": "PUBLIC"
                },
                "resources": {
                    "cpu": "0.5 vCPU",
                    "memory": "1 GB"
                },
                "scaling": {
                    "min_instances": 1,
                    "max_instances": 3,
                    "target_utilization": 80
                },
                "health_check": {
                    "interval": 30,
                    "timeout": 5,
                    "retries": 3
                },
                "ports": {
                    "http": 8080,
                    "metrics": 9090
                },
                "docker": {
                    "restart_policy": "unless-stopped",
                    "cpu_limit": "1.0",
                    "memory_limit": "2G",
                    "cpu_reservation": "0.5",
                    "memory_reservation": "1G"
                },
                "monitoring": {
                    "retention_days": 7
                },
                "alarms": {
                    "error_rate_threshold": 0.1,
                    "response_time_threshold": 10.0,
                    "throughput_threshold": 1.0
                },
                "validation": {
                    "max_response_time_ms": 10000,
                    "max_error_rate": 0.1,
                    "min_uptime_percentage": 95.0,
                    "alert_thresholds": {
                        "cpu_usage": 90,
                        "memory_usage": 90
                    }
                },
                "testing": {
                    "concurrent_users": 5,
                    "duration_minutes": 5,
                    "ramp_up_time_seconds": 30,
                    "max_concurrent_users": 10,
                    "stress_duration_minutes": 2
                }
            },
            "staging": {
                "mcp_endpoints": {
                    "search": "https://staging-search-mcp.agentcore.aws",
                    "reasoning": "https://staging-reasoning-mcp.agentcore.aws"
                },
                "mcp_settings": {
                    "connection_timeout": 30,
                    "retry_attempts": 3
                },
                "cognito": {
                    "user_pool_id_placeholder": "us-east-1_staging789"
                },
                "auth": {
                    "token_cache_ttl": 600
                },
                "cache": {
                    "enabled": True,
                    "ttl": 900,
                    "redis_url": "redis://staging-redis.cache.amazonaws.com:6379"
                },
                "agent": {
                    "model": "amazon.nova-pro-v1:0:300k",
                    "temperature": 0.1,
                    "max_tokens": 4096
                },
                "logging": {
                    "level": "INFO",
                    "format": "json",
                    "retention_days": 30,
                    "max_size": "50m",
                    "max_files": 5
                },
                "observability": {
                    "enabled": True,
                    "tracing": True,
                    "metrics": True,
                    "logs": True
                },
                "knowledge_base": {
                    "model": "amazon.nova-pro-v1:0",
                    "max_results": 25,
                    "search_type": "HYBRID",
                    "temperature": 0.1,
                    "max_tokens": 4096
                },
                "debug": False,
                "mock_mcp_servers": False,
                "performance": {
                    "max_concurrent_requests": 50,
                    "request_timeout": 30,
                    "circuit_breaker_enabled": True
                },
                "security": {
                    "rate_limiting_enabled": True,
                    "max_requests_per_minute": 200,
                    "burst_limit": 50,
                    "security_headers_enabled": True,
                    "cors": {
                        "allowed_origins": ["https://staging.example.com"]
                    },
                    "data_retention_days": 90,
                    "audit_retention_days": 180
                },
                "network": {
                    "mode": "PUBLIC"
                },
                "resources": {
                    "cpu": "1 vCPU",
                    "memory": "2 GB"
                },
                "scaling": {
                    "min_instances": 1,
                    "max_instances": 10,
                    "target_utilization": 70
                },
                "health_check": {
                    "interval": 30,
                    "timeout": 5,
                    "retries": 3
                },
                "ports": {
                    "http": 8080,
                    "metrics": 9090
                },
                "docker": {
                    "restart_policy": "unless-stopped",
                    "cpu_limit": "2.0",
                    "memory_limit": "4G",
                    "cpu_reservation": "1.0",
                    "memory_reservation": "2G"
                },
                "monitoring": {
                    "retention_days": 30
                },
                "alarms": {
                    "error_rate_threshold": 0.05,
                    "response_time_threshold": 5.0,
                    "throughput_threshold": 5.0
                },
                "validation": {
                    "max_response_time_ms": 5000,
                    "max_error_rate": 0.05,
                    "min_uptime_percentage": 98.0,
                    "alert_thresholds": {
                        "cpu_usage": 80,
                        "memory_usage": 80
                    }
                },
                "testing": {
                    "concurrent_users": 20,
                    "duration_minutes": 10,
                    "ramp_up_time_seconds": 60,
                    "max_concurrent_users": 50,
                    "stress_duration_minutes": 5
                }
            },
            "production": {
                "mcp_endpoints": {
                    "search": "https://restaurant_search_conversational_agent-dsuHTs5FJn.agentcore.us-east-1.amazonaws.com",
                    "reasoning": "https://restaurant_reasoning_mcp-UFz1VQCFu1.agentcore.us-east-1.amazonaws.com"
                },
                "mcp_settings": {
                    "connection_timeout": 45,
                    "retry_attempts": 5
                },
                "cognito": {
                    "user_pool_id_placeholder": "us-east-1_prod456789"
                },
                "auth": {
                    "token_cache_ttl": 1800
                },
                "cache": {
                    "enabled": True,
                    "ttl": 1800,
                    "redis_url": "redis://prod-redis.cache.amazonaws.com:6379"
                },
                "agent": {
                    "model": "amazon.nova-pro-v1:0:300k",
                    "temperature": 0.1,
                    "max_tokens": 4096
                },
                "logging": {
                    "level": "INFO",
                    "format": "json",
                    "retention_days": 90,
                    "max_size": "100m",
                    "max_files": 10
                },
                "observability": {
                    "enabled": True,
                    "tracing": True,
                    "metrics": True,
                    "logs": True
                },
                "knowledge_base": {
                    "model": "amazon.nova-pro-v1:0",
                    "max_results": 30,
                    "search_type": "HYBRID",
                    "temperature": 0.1,
                    "max_tokens": 4096
                },
                "debug": False,
                "mock_mcp_servers": False,
                "performance": {
                    "max_concurrent_requests": 100,
                    "request_timeout": 45,
                    "circuit_breaker_enabled": True
                },
                "security": {
                    "rate_limiting_enabled": True,
                    "max_requests_per_minute": 500,
                    "burst_limit": 100,
                    "security_headers_enabled": True,
                    "cors": {
                        "allowed_origins": ["https://app.example.com", "https://www.example.com"]
                    },
                    "data_retention_days": 365,
                    "audit_retention_days": 2555  # 7 years
                },
                "network": {
                    "mode": "PUBLIC"
                },
                "resources": {
                    "cpu": "2 vCPU",
                    "memory": "4 GB"
                },
                "scaling": {
                    "min_instances": 2,
                    "max_instances": 20,
                    "target_utilization": 70
                },
                "health_check": {
                    "interval": 30,
                    "timeout": 5,
                    "retries": 3
                },
                "ports": {
                    "http": 8080,
                    "metrics": 9090
                },
                "docker": {
                    "restart_policy": "unless-stopped",
                    "cpu_limit": "4.0",
                    "memory_limit": "8G",
                    "cpu_reservation": "2.0",
                    "memory_reservation": "4G"
                },
                "monitoring": {
                    "retention_days": 90
                },
                "alarms": {
                    "error_rate_threshold": 0.02,
                    "response_time_threshold": 3.0,
                    "throughput_threshold": 10.0
                },
                "validation": {
                    "max_response_time_ms": 3000,
                    "max_error_rate": 0.02,
                    "min_uptime_percentage": 99.5,
                    "alert_thresholds": {
                        "cpu_usage": 70,
                        "memory_usage": 70
                    }
                },
                "testing": {
                    "concurrent_users": 100,
                    "duration_minutes": 30,
                    "ramp_up_time_seconds": 300,
                    "max_concurrent_users": 200,
                    "stress_duration_minutes": 10
                }
            }
        }
        
        return configs.get(environment, configs["development"])
    
    def save_generation_report(self, generation_results: Dict[str, Any], output_file: Optional[str] = None) -> str:
        """Save generation report to file."""
        if not output_file:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            output_file = f"deployment_config_generation_report_{timestamp}.json"
        
        try:
            with open(output_file, 'w') as f:
                json.dump(generation_results, f, indent=2, default=str)
            
            logger.info(f"Generation report saved to: {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Failed to save generation report: {e}")
            raise


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Generate environment-specific deployment configurations'
    )
    parser.add_argument('--environment',
                       choices=['development', 'staging', 'production', 'all'],
                       default='all',
                       help='Environment to generate config for')
    parser.add_argument('--agent-name', default='mbti-travel-assistant-mcp',
                       help='Agent name')
    parser.add_argument('--region', default='us-east-1',
                       help='AWS region')
    parser.add_argument('--account-id',
                       help='AWS account ID (optional)')
    parser.add_argument('--output-file',
                       help='Output file for generation report')
    
    args = parser.parse_args()
    
    try:
        generator = DeploymentConfigGenerator()
        
        if args.environment == 'all':
            result = generator.generate_all_environment_configs(
                agent_name=args.agent_name,
                region=args.region,
                account_id=args.account_id
            )
        else:
            result = generator.generate_environment_config(
                environment=args.environment,
                agent_name=args.agent_name,
                region=args.region,
                account_id=args.account_id
            )
            
            # Wrap single environment result in the expected format
            result = {
                "timestamp": datetime.utcnow().isoformat(),
                "agent_name": args.agent_name,
                "region": args.region,
                "account_id": args.account_id,
                "environments": {args.environment: result},
                "summary": {
                    "total_environments": 1,
                    "successful_environments": 1 if result.get("success", False) else 0,
                    "failed_environments": 0 if result.get("success", False) else 1,
                    "success_rate": 100.0 if result.get("success", False) else 0.0
                }
            }
        
        # Save generation report
        report_file = generator.save_generation_report(result, args.output_file)
        
        if result["summary"]["success_rate"] == 100.0:
            print("\n" + "="*60)
            print("🎉 CONFIGURATION GENERATION SUCCESSFUL! 🎉")
            print("="*60)
            print(f"Agent Name: {args.agent_name}")
            print(f"Region: {args.region}")
            print(f"Environments: {', '.join(result['environments'].keys())}")
            print(f"Success Rate: {result['summary']['success_rate']:.1f}%")
            print(f"Report File: {report_file}")
            print("="*60)
            return 0
        else:
            print("\n" + "="*60)
            print("⚠️ CONFIGURATION GENERATION COMPLETED WITH ISSUES")
            print("="*60)
            print(f"Success Rate: {result['summary']['success_rate']:.1f}%")
            print(f"Failed Environments: {result['summary']['failed_environments']}")
            print(f"Report File: {report_file}")
            print("="*60)
            return 1
            
    except Exception as e:
        logger.error(f"Configuration generation failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())