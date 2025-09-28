# REQUIRED: ARM64 platform for Amazon Bedrock AgentCore Runtime
FROM --platform=linux/arm64 ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# Configure UV for container environment
ENV UV_SYSTEM_PYTHON=1 UV_COMPILE_BYTECODE=1

# Install system dependencies for health checks and monitoring
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    procps \
    net-tools \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt requirements.txt
RUN uv pip install -r requirements.txt

# Install observability and monitoring tools
RUN uv pip install \
    aws-opentelemetry-distro>=0.10.1 \
    prometheus-client>=0.20.0 \
    psutil>=5.9.0

# Set environment variables
ENV AWS_REGION=us-east-1
ENV AWS_DEFAULT_REGION=us-east-1
ENV DOCKER_CONTAINER=1
ENV LOG_LEVEL=INFO
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Create non-root user for security
RUN useradd -m -u 1000 agentcore && \
    mkdir -p /app/logs /app/data /app/cache && \
    chown -R agentcore:agentcore /app

# Switch to non-root user
USER agentcore

# Copy application code
COPY --chown=agentcore:agentcore . .

# Create health check script
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
# Check if main process is running\n\
if ! pgrep -f "python main.py" > /dev/null; then\n\
    echo "Main process not running"\n\
    exit 1\n\
fi\n\
\n\
# Check AgentCore runtime health endpoint\n\
if ! curl -f -s http://localhost:8080/health > /dev/null 2>&1; then\n\
    echo "AgentCore runtime health check failed"\n\
    exit 1\n\
fi\n\
\n\
# Check if we can connect to MCP endpoints (if configured)\n\
if [ -n "$SEARCH_MCP_ENDPOINT" ] && [ "$SEARCH_MCP_ENDPOINT" != "http://localhost:8001" ]; then\n\
    if ! curl -f -s --connect-timeout 5 "$SEARCH_MCP_ENDPOINT/health" > /dev/null 2>&1; then\n\
        echo "Warning: Search MCP endpoint health check failed"\n\
    fi\n\
fi\n\
\n\
echo "Health check passed"\n\
exit 0' > /app/health_check.sh && chmod +x /app/health_check.sh

# Expose ports
EXPOSE 8080 8000 9090

# Health check with comprehensive monitoring
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD /app/health_check.sh

# Start AgentCore Runtime with observability
CMD ["opentelemetry-instrument", "python", "main.py"]