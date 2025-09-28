# Docker Compose deployment script for MBTI Travel Assistant MCP (PowerShell)
# This script manages deployment using docker-compose for different environments on Windows

param(
    [Parameter(Position=0)]
    [ValidateSet("start", "stop", "restart", "build", "status", "logs", "health", "cleanup")]
    [string]$Command,
    
    [Parameter()]
    [ValidateSet("development", "staging", "production")]
    [string]$Environment = "development",
    
    [Parameter()]
    [string]$Service = "",
    
    [Parameter()]
    [switch]$Follow,
    
    [Parameter()]
    [switch]$Help
)

# Configuration
$ComposeProjectName = "mbti-travel-assistant"
$ComposeFile = "docker-compose.yml"
$ComposeFileProd = "docker-compose.prod.yml"

# Function to write colored output
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] " -NoNewline -ForegroundColor Gray
    Write-Host $Message -ForegroundColor $Color
}

function Write-Info {
    param([string]$Message)
    Write-ColorOutput "[INFO] $Message" "Cyan"
}

function Write-Success {
    param([string]$Message)
    Write-ColorOutput "[SUCCESS] $Message" "Green"
}

function Write-Warning {
    param([string]$Message)
    Write-ColorOutput "[WARNING] $Message" "Yellow"
}

function Write-Error {
    param([string]$Message)
    Write-ColorOutput "[ERROR] $Message" "Red"
}

# Function to check prerequisites
function Test-Prerequisites {
    Write-Info "Checking prerequisites..."
    
    # Check if Docker is installed and running
    try {
        $dockerVersion = docker --version
        Write-Info "Docker found: $dockerVersion"
    }
    catch {
        Write-Error "Docker is not installed or not in PATH"
        exit 1
    }
    
    # Check if Docker Compose is installed
    try {
        $composeVersion = docker-compose --version
        Write-Info "Docker Compose found: $composeVersion"
    }
    catch {
        try {
            $composeVersion = docker compose version
            Write-Info "Docker Compose (plugin) found: $composeVersion"
        }
        catch {
            Write-Error "Docker Compose is not installed"
            exit 1
        }
    }
    
    # Check if Docker daemon is running
    try {
        docker info | Out-Null
        Write-Success "Docker daemon is running"
    }
    catch {
        Write-Error "Docker daemon is not running"
        exit 1
    }
    
    Write-Success "Prerequisites check passed"
}

# Function to validate environment configuration
function Test-EnvironmentConfiguration {
    Write-Info "Validating environment configuration for: $Environment"
    
    # Check if environment configuration exists
    $envFile = "config\environments\$Environment.env"
    if (-not (Test-Path $envFile)) {
        Write-Error "Environment configuration file not found: $envFile"
        exit 1
    }
    
    # Validate required environment variables for production
    if ($Environment -eq "production") {
        $requiredVars = @(
            "SEARCH_MCP_ENDPOINT",
            "REASONING_MCP_ENDPOINT", 
            "COGNITO_USER_POOL_ID",
            "JWT_AUDIENCE"
        )
        
        foreach ($var in $requiredVars) {
            $value = [Environment]::GetEnvironmentVariable($var)
            if ([string]::IsNullOrEmpty($value)) {
                Write-Error "Required environment variable not set: $var"
                exit 1
            }
        }
    }
    
    Write-Success "Environment configuration validated"
}

# Function to select compose file based on environment
function Select-ComposeFile {
    if ($Environment -eq "production") {
        $script:ComposeFile = $ComposeFileProd
        Write-Info "Using production compose file: $ComposeFile"
    }
    else {
        Write-Info "Using development compose file: $ComposeFile"
    }
    
    if (-not (Test-Path $ComposeFile)) {
        Write-Error "Compose file not found: $ComposeFile"
        exit 1
    }
}

# Function to load environment variables
function Import-EnvironmentVariables {
    Write-Info "Loading environment variables..."
    
    # Load base .env file if it exists
    if (Test-Path ".env") {
        Get-Content ".env" | ForEach-Object {
            if ($_ -match "^([^#][^=]+)=(.*)$") {
                [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
            }
        }
        Write-Info "Loaded base .env file"
    }
    
    # Load environment-specific configuration
    $envFile = "config\environments\$Environment.env"
    if (Test-Path $envFile) {
        Get-Content $envFile | ForEach-Object {
            if ($_ -match "^([^#][^=]+)=(.*)$") {
                [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
            }
        }
        Write-Info "Loaded environment-specific configuration: $envFile"
    }
    
    # Set environment variables for docker-compose
    [Environment]::SetEnvironmentVariable("ENVIRONMENT", $Environment, "Process")
    [Environment]::SetEnvironmentVariable("COMPOSE_PROJECT_NAME", $ComposeProjectName, "Process")
}

# Function to build images
function Build-Images {
    Write-Info "Building Docker images..."
    
    try {
        docker-compose -f $ComposeFile -p $ComposeProjectName build
        Write-Success "Docker images built successfully"
    }
    catch {
        try {
            docker compose -f $ComposeFile -p $ComposeProjectName build
            Write-Success "Docker images built successfully"
        }
        catch {
            Write-Error "Failed to build Docker images: $_"
            exit 1
        }
    }
}

# Function to start services
function Start-Services {
    Write-Info "Starting services..."
    
    try {
        docker-compose -f $ComposeFile -p $ComposeProjectName up -d
        Write-Success "Services started successfully"
    }
    catch {
        try {
            docker compose -f $ComposeFile -p $ComposeProjectName up -d
            Write-Success "Services started successfully"
        }
        catch {
            Write-Error "Failed to start services: $_"
            exit 1
        }
    }
}

# Function to stop services
function Stop-Services {
    Write-Info "Stopping services..."
    
    try {
        docker-compose -f $ComposeFile -p $ComposeProjectName down
        Write-Success "Services stopped successfully"
    }
    catch {
        try {
            docker compose -f $ComposeFile -p $ComposeProjectName down
            Write-Success "Services stopped successfully"
        }
        catch {
            Write-Error "Failed to stop services: $_"
            exit 1
        }
    }
}

# Function to restart services
function Restart-Services {
    Write-Info "Restarting services..."
    
    Stop-Services
    Start-Services
    
    Write-Success "Services restarted successfully"
}

# Function to show service status
function Show-Status {
    Write-Info "Service status:"
    
    try {
        docker-compose -f $ComposeFile -p $ComposeProjectName ps
    }
    catch {
        try {
            docker compose -f $ComposeFile -p $ComposeProjectName ps
        }
        catch {
            Write-Error "Failed to get service status: $_"
        }
    }
}

# Function to show service logs
function Show-Logs {
    param(
        [string]$ServiceName,
        [bool]$FollowLogs
    )
    
    if ($ServiceName) {
        Write-Info "Showing logs for service: $ServiceName"
        if ($FollowLogs) {
            try {
                docker-compose -f $ComposeFile -p $ComposeProjectName logs -f $ServiceName
            }
            catch {
                docker compose -f $ComposeFile -p $ComposeProjectName logs -f $ServiceName
            }
        }
        else {
            try {
                docker-compose -f $ComposeFile -p $ComposeProjectName logs $ServiceName
            }
            catch {
                docker compose -f $ComposeFile -p $ComposeProjectName logs $ServiceName
            }
        }
    }
    else {
        Write-Info "Showing logs for all services"
        try {
            docker-compose -f $ComposeFile -p $ComposeProjectName logs
        }
        catch {
            docker compose -f $ComposeFile -p $ComposeProjectName logs
        }
    }
}

# Function to run health checks
function Test-ServiceHealth {
    Write-Info "Running health checks..."
    
    # Wait for services to start
    Start-Sleep -Seconds 30
    
    # Check main service health
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8080/health" -UseBasicParsing -TimeoutSec 10
        if ($response.StatusCode -eq 200) {
            Write-Success "Main service health check passed"
        }
        else {
            Write-Error "Main service health check failed with status: $($response.StatusCode)"
            return $false
        }
    }
    catch {
        Write-Error "Main service health check failed: $_"
        return $false
    }
    
    # Check Redis health (if running)
    $redisContainer = docker ps --format "table {{.Names}}" | Select-String "mbti-redis"
    if ($redisContainer) {
        try {
            $pingResult = docker exec mbti-redis redis-cli ping
            if ($pingResult -eq "PONG") {
                Write-Success "Redis health check passed"
            }
            else {
                Write-Warning "Redis health check failed"
            }
        }
        catch {
            Write-Warning "Redis health check failed: $_"
        }
    }
    
    # Check Prometheus health (if running)
    $prometheusContainer = docker ps --format "table {{.Names}}" | Select-String "prometheus"
    if ($prometheusContainer) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:9091/-/healthy" -UseBasicParsing -TimeoutSec 10
            if ($response.StatusCode -eq 200) {
                Write-Success "Prometheus health check passed"
            }
            else {
                Write-Warning "Prometheus health check failed"
            }
        }
        catch {
            Write-Warning "Prometheus health check failed: $_"
        }
    }
    
    Write-Success "Health checks completed"
    return $true
}

# Function to clean up resources
function Remove-Resources {
    Write-Info "Cleaning up resources..."
    
    # Stop and remove containers
    try {
        docker-compose -f $ComposeFile -p $ComposeProjectName down -v --remove-orphans
    }
    catch {
        docker compose -f $ComposeFile -p $ComposeProjectName down -v --remove-orphans
    }
    
    # Remove unused images
    docker image prune -f
    
    Write-Success "Cleanup completed"
}

# Function to display usage
function Show-Usage {
    Write-Host @"
Usage: .\deploy_docker.ps1 [COMMAND] [OPTIONS]

Commands:
  start                  Start all services
  stop                   Stop all services
  restart                Restart all services
  build                  Build Docker images
  status                 Show service status
  logs [SERVICE]         Show logs (optionally for specific service)
  health                 Run health checks
  cleanup                Clean up resources

Options:
  -Environment ENV       Environment (development, staging, production)
  -Service SERVICE       Service name (for logs command)
  -Follow               Follow logs (for logs command)
  -Help                 Show this help message

Examples:
  .\deploy_docker.ps1 start                                    # Start development environment
  .\deploy_docker.ps1 start -Environment production           # Start production environment
  .\deploy_docker.ps1 logs -Service mbti-travel-assistant -Follow  # Follow logs for main service
  .\deploy_docker.ps1 health                                  # Run health checks
"@
}

# Main execution
function Main {
    if ($Help) {
        Show-Usage
        exit 0
    }
    
    if (-not $Command) {
        Write-Error "No command specified"
        Show-Usage
        exit 1
    }
    
    Write-Info "MBTI Travel Assistant MCP Deployment"
    Write-Info "Environment: $Environment"
    Write-Info "Command: $Command"
    
    Test-Prerequisites
    Test-EnvironmentConfiguration
    Select-ComposeFile
    Import-EnvironmentVariables
    
    switch ($Command) {
        "start" {
            Build-Images
            Start-Services
            Test-ServiceHealth
        }
        "stop" {
            Stop-Services
        }
        "restart" {
            Restart-Services
            Test-ServiceHealth
        }
        "build" {
            Build-Images
        }
        "status" {
            Show-Status
        }
        "logs" {
            Show-Logs -ServiceName $Service -FollowLogs $Follow
        }
        "health" {
            Test-ServiceHealth
        }
        "cleanup" {
            Remove-Resources
        }
        default {
            Write-Error "Unknown command: $Command"
            Show-Usage
            exit 1
        }
    }
    
    Write-Success "Deployment command completed successfully!"
}

# Run main function
Main