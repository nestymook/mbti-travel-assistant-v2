"""
AgentCore Gateway for MCP Tools

FastAPI application that exposes restaurant search and reasoning MCP tools
through RESTful HTTP endpoints with JWT authentication.
"""

from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
import structlog
import os

from middleware.auth_middleware import AuthenticationMiddleware, get_current_user
from middleware.observability_middleware import ObservabilityMiddleware
from middleware.jwt_validator import UserContext
from config.settings import get_settings
from api.restaurant_endpoints import router as restaurant_router
from api.tool_metadata_endpoints import router as tool_metadata_router
from api.observability_endpoints import router as observability_router
from api.config_endpoints import router as config_router
from services.mcp_client_manager import get_mcp_client_manager, shutdown_mcp_client_manager
from services.observability_service import get_observability_service, shutdown_observability_service
from services.config_manager import initialize_config_manager, get_config_manager, shutdown_config_manager
from services.config_validator import get_config_validator

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Get application settings
settings = get_settings()

# Create FastAPI application
app = FastAPI(
    title="AgentCore Gateway for MCP Tools",
    description="RESTful API Gateway for restaurant search and reasoning MCP tools",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.app.cors_origins,
    allow_credentials=settings.app.cors_allow_credentials,
    allow_methods=settings.app.cors_allow_methods,
    allow_headers=settings.app.cors_allow_headers,
)

# Add observability middleware (first to track all requests)
app.add_middleware(
    ObservabilityMiddleware,
    bypass_paths=settings.app.bypass_paths
)

# Add authentication middleware
app.add_middleware(
    AuthenticationMiddleware,
    bypass_paths=settings.app.bypass_paths
)

# Include API routers
app.include_router(restaurant_router)
app.include_router(tool_metadata_router)
app.include_router(observability_router)
app.include_router(config_router)

# Health check endpoint is now handled by observability_endpoints.py

@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "AgentCore Gateway for MCP Tools",
        "version": "1.0.0",
        "description": "RESTful API Gateway for restaurant search and reasoning MCP tools",
        "authentication": "bypass",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "metrics": "/metrics",
            "tools_metadata": "/tools/metadata",
            "configuration": "/config/current",
            "reload_config": "/config/reload",
            "validate_config": "/config/validate"
        }
    }

@app.get("/auth/test")
async def test_authentication(
    request: Request,
    current_user: UserContext = Depends(get_current_user)
):
    """Test endpoint to verify authentication is working."""
    return {
        "message": "Authentication successful",
        "user": {
            "user_id": current_user.user_id,
            "username": current_user.username,
            "email": current_user.email,
            "authenticated_at": current_user.authenticated_at.isoformat()
        },
        "token_claims": {
            "sub": current_user.token_claims.get("sub"),
            "token_use": current_user.token_claims.get("token_use"),
            "aud": current_user.token_claims.get("aud"),
            "iss": current_user.token_claims.get("iss")
        }
    }


@app.on_event("startup")
async def startup_event():
    """Initialize services on application startup."""
    logger.info("Starting AgentCore Gateway services")
    
    # Initialize configuration management
    environment = os.getenv('ENVIRONMENT', 'development')
    config = await initialize_config_manager(environment)
    logger.info("Configuration loaded", environment=config.name, hot_reload=config.enable_hot_reload)
    
    # Validate configuration on startup
    validator = get_config_validator()
    is_valid, errors, warnings = await validator.validate_configuration(config)
    
    if not is_valid:
        logger.error("Configuration validation failed", errors=errors)
        raise RuntimeError(f"Invalid configuration: {'; '.join(errors)}")
    
    if warnings:
        logger.warning("Configuration validation warnings", warnings=warnings)
    
    # Initialize observability service
    get_observability_service()
    
    # Initialize MCP client manager
    await get_mcp_client_manager()
    
    logger.info("AgentCore Gateway services started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup services on application shutdown."""
    logger.info("Shutting down AgentCore Gateway services")
    
    # Shutdown MCP client manager
    await shutdown_mcp_client_manager()
    
    # Shutdown observability service
    shutdown_observability_service()
    
    # Shutdown configuration manager
    shutdown_config_manager()
    
    logger.info("AgentCore Gateway services shut down successfully")

if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8080"))
    log_level = os.getenv("LOG_LEVEL", "info").lower()
    
    logger.info(
        "Starting AgentCore Gateway",
        host=host,
        port=port,
        log_level=log_level
    )
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        log_level=log_level,
        reload=False
    )