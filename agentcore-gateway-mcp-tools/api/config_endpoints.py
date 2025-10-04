"""
Configuration management API endpoints.

This module provides REST endpoints for configuration management including:
- Getting current configuration
- Reloading configuration
- Validating configuration
- Managing MCP server configurations
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import Dict, Any, List
import structlog

from middleware.jwt_validator import UserContext
from middleware.auth_middleware import get_current_user
from services.config_manager import get_config_manager, EnvironmentConfig, MCPServerConfig
from services.config_validator import get_config_validator, validate_all_environment_configs
from models.response_models import SuccessResponse, ErrorResponse

logger = structlog.get_logger(__name__)

router = APIRouter(
    prefix="/config",
    tags=["Configuration Management"],
    responses={
        401: {"model": ErrorResponse, "description": "Authentication required"},
        403: {"model": ErrorResponse, "description": "Insufficient permissions"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)


@router.get("/current", response_model=Dict[str, Any])
async def get_current_configuration(
    current_user: UserContext = Depends(get_current_user)
):
    """
    Get the current configuration.
    
    Returns the currently loaded configuration including all MCP server settings.
    """
    try:
        config_manager = get_config_manager()
        current_config = config_manager.get_current_config()
        
        if not current_config:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Configuration not loaded"
            )
        
        logger.info("Configuration retrieved", user_id=current_user.user_id)
        
        return {
            "success": True,
            "data": {
                "environment": current_config.name,
                "debug": current_config.debug,
                "log_level": current_config.log_level,
                "enable_hot_reload": current_config.enable_hot_reload,
                "mcp_servers": {
                    name: {
                        "name": server.name,
                        "url": server.url,
                        "timeout": server.timeout,
                        "max_retries": server.max_retries,
                        "retry_delay": server.retry_delay,
                        "health_check_path": server.health_check_path,
                        "enabled": server.enabled,
                        "tools": server.tools
                    }
                    for name, server in current_config.mcp_servers.items()
                }
            }
        }
        
    except Exception as e:
        logger.error("Failed to get current configuration", error=str(e), user_id=current_user.user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get configuration: {str(e)}"
        )


@router.post("/reload", response_model=SuccessResponse)
async def reload_configuration(
    current_user: UserContext = Depends(get_current_user)
):
    """
    Reload configuration from files.
    
    Triggers a reload of the configuration from the configuration files.
    This is useful when configuration files have been updated.
    """
    try:
        config_manager = get_config_manager()
        await config_manager.reload_configuration()
        
        # Validate the reloaded configuration
        current_config = config_manager.get_current_config()
        if current_config:
            validator = get_config_validator()
            is_valid, errors, warnings = await validator.validate_configuration(current_config)
            
            if not is_valid:
                logger.error("Reloaded configuration is invalid", errors=errors, user_id=current_user.user_id)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid configuration after reload: {'; '.join(errors)}"
                )
            
            if warnings:
                logger.warning("Configuration validation warnings", warnings=warnings, user_id=current_user.user_id)
        
        logger.info("Configuration reloaded successfully", user_id=current_user.user_id)
        
        return SuccessResponse(
            success=True,
            message="Configuration reloaded successfully",
            data={
                "environment": current_config.name if current_config else None,
                "timestamp": "now"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to reload configuration", error=str(e), user_id=current_user.user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reload configuration: {str(e)}"
        )


@router.get("/validate", response_model=Dict[str, Any])
async def validate_current_configuration(
    current_user: UserContext = Depends(get_current_user)
):
    """
    Validate the current configuration.
    
    Performs comprehensive validation of the current configuration including
    connectivity checks to MCP servers.
    """
    try:
        config_manager = get_config_manager()
        current_config = config_manager.get_current_config()
        
        if not current_config:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Configuration not loaded"
            )
        
        validator = get_config_validator()
        is_valid, errors, warnings = await validator.validate_configuration(current_config)
        
        # Also validate server connectivity
        connectivity_results = {}
        for server_name, server_config in current_config.mcp_servers.items():
            is_reachable, error_msg = await validator.validate_server_connectivity(server_config)
            connectivity_results[server_name] = {
                "reachable": is_reachable,
                "error": error_msg
            }
        
        logger.info("Configuration validation completed", 
                   is_valid=is_valid, 
                   error_count=len(errors),
                   warning_count=len(warnings),
                   user_id=current_user.user_id)
        
        return {
            "success": True,
            "data": {
                "is_valid": is_valid,
                "errors": errors,
                "warnings": warnings,
                "connectivity": connectivity_results,
                "environment": current_config.name
            }
        }
        
    except Exception as e:
        logger.error("Failed to validate configuration", error=str(e), user_id=current_user.user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate configuration: {str(e)}"
        )


@router.get("/validate/all", response_model=Dict[str, Any])
async def validate_all_configurations(
    current_user: UserContext = Depends(get_current_user)
):
    """
    Validate all environment configuration files.
    
    Validates configuration files for all environments (development, staging, production, test).
    """
    try:
        results = await validate_all_environment_configs()
        
        summary = {
            "total_environments": len(results),
            "valid_environments": sum(1 for is_valid, _, _ in results.values() if is_valid),
            "invalid_environments": sum(1 for is_valid, _, _ in results.values() if not is_valid)
        }
        
        detailed_results = {}
        for env_name, (is_valid, errors, warnings) in results.items():
            detailed_results[env_name] = {
                "is_valid": is_valid,
                "errors": errors,
                "warnings": warnings
            }
        
        logger.info("All configurations validated", 
                   summary=summary,
                   user_id=current_user.user_id)
        
        return {
            "success": True,
            "data": {
                "summary": summary,
                "results": detailed_results
            }
        }
        
    except Exception as e:
        logger.error("Failed to validate all configurations", error=str(e), user_id=current_user.user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate configurations: {str(e)}"
        )


@router.get("/servers", response_model=Dict[str, Any])
async def get_mcp_servers(
    current_user: UserContext = Depends(get_current_user)
):
    """
    Get all MCP server configurations.
    
    Returns detailed information about all configured MCP servers.
    """
    try:
        config_manager = get_config_manager()
        servers = config_manager.get_all_mcp_servers()
        
        server_info = {}
        for name, server in servers.items():
            server_info[name] = {
                "name": server.name,
                "url": server.url,
                "timeout": server.timeout,
                "max_retries": server.max_retries,
                "retry_delay": server.retry_delay,
                "health_check_path": server.health_check_path,
                "enabled": server.enabled,
                "tools": server.tools
            }
        
        logger.info("MCP servers retrieved", server_count=len(servers), user_id=current_user.user_id)
        
        return {
            "success": True,
            "data": {
                "servers": server_info,
                "total_servers": len(servers),
                "enabled_servers": sum(1 for s in servers.values() if s.enabled)
            }
        }
        
    except Exception as e:
        logger.error("Failed to get MCP servers", error=str(e), user_id=current_user.user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get MCP servers: {str(e)}"
        )


@router.get("/servers/{server_name}", response_model=Dict[str, Any])
async def get_mcp_server(
    server_name: str,
    current_user: UserContext = Depends(get_current_user)
):
    """
    Get configuration for a specific MCP server.
    
    Returns detailed configuration for the specified MCP server.
    """
    try:
        config_manager = get_config_manager()
        server_config = config_manager.get_mcp_server_config(server_name)
        
        if not server_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"MCP server '{server_name}' not found"
            )
        
        # Test server connectivity
        validator = get_config_validator()
        is_reachable, error_msg = await validator.validate_server_connectivity(server_config)
        
        logger.info("MCP server retrieved", server_name=server_name, user_id=current_user.user_id)
        
        return {
            "success": True,
            "data": {
                "name": server_config.name,
                "url": server_config.url,
                "timeout": server_config.timeout,
                "max_retries": server_config.max_retries,
                "retry_delay": server_config.retry_delay,
                "health_check_path": server_config.health_check_path,
                "enabled": server_config.enabled,
                "tools": server_config.tools,
                "connectivity": {
                    "reachable": is_reachable,
                    "error": error_msg
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get MCP server", server_name=server_name, error=str(e), user_id=current_user.user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get MCP server: {str(e)}"
        )