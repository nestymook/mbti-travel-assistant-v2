# REQUIRED: ARM64 platform for Amazon Bedrock AgentCore Runtime
FROM --platform=linux/arm64 ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Set working directory
WORKDIR /app

# Configure UV for container environment
ENV UV_SYSTEM_PYTHON=1 UV_COMPILE_BYTECODE=1

# Install system dependencies for health checks and monitoring
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt requirements.txt

# Install Python dependencies
RUN uv pip install -r requirements.txt

# Install observability tools
RUN uv pip install aws-opentelemetry-distro>=0.10.1

# Set AWS region environment variables
ENV AWS_REGION=us-east-1
ENV AWS_DEFAULT_REGION=us-east-1

# Signal that this is running in Docker for host binding logic
ENV DOCKER_CONTAINER=1

# Create non-root user for security
RUN useradd -m -u 1000 bedrock_agentcore

# Create necessary directories with proper permissions
RUN mkdir -p /app/logs /app/data /app/cache /app/tmp && \
    chown -R bedrock_agentcore:bedrock_agentcore /app

# Copy application code (respecting .dockerignore)
COPY --chown=bedrock_agentcore:bedrock_agentcore . .

# Copy and set up health check script
COPY --chown=bedrock_agentcore:bedrock_agentcore scripts/docker_health_check.sh /app/health_check.sh
RUN chmod +x /app/health_check.sh

# Switch to non-root user
USER bedrock_agentcore

# Expose ports
EXPOSE 8080  # AgentCore Runtime
EXPOSE 8000  # MCP Server (if needed)
EXPOSE 9090  # Metrics endpoint

# Add health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD /app/health_check.sh

# Start application with observability instrumentation
CMD ["opentelemetry-instrument", "python", "-m", "main"]
