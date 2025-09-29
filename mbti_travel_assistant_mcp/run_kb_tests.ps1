#!/usr/bin/env powershell
<#
.SYNOPSIS
    Quick Knowledge Base Testing PowerShell Script

.DESCRIPTION
    Provides easy testing of the OpenSearch Knowledge Base functionality
    for the MBTI Travel Assistant project.

.PARAMETER TestType
    Type of test to run: connectivity, mbti, geographic, performance, all (default)

.EXAMPLE
    .\run_kb_tests.ps1
    .\run_kb_tests.ps1 -TestType mbti
    .\run_kb_tests.ps1 -TestType connectivity

.NOTES
    Requires Python, boto3, and AWS credentials to be configured
#>

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("connectivity", "mbti", "geographic", "performance", "all")]
    [string]$TestType = "all"
)

# Function to check prerequisites
function Test-Prerequisites {
    Write-Host "🔍 Checking prerequisites..." -ForegroundColor Cyan
    
    # Check Python
    try {
        $pythonVersion = python --version 2>&1
        Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ Python not found. Please install Python and add to PATH." -ForegroundColor Red
        return $false
    }
    
    # Check boto3
    try {
        python -c "import boto3" 2>&1 | Out-Null
        Write-Host "✅ boto3 library found" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ boto3 not found. Install with: pip install boto3" -ForegroundColor Red
        return $false
    }
    
    # Check AWS credentials
    try {
        aws sts get-caller-identity 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ AWS credentials configured" -ForegroundColor Green
        } else {
            Write-Host "⚠️  AWS credentials not configured or AWS CLI not available" -ForegroundColor Yellow
            Write-Host "   Tests may fail without proper AWS credentials" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "⚠️  Could not verify AWS credentials" -ForegroundColor Yellow
    }
    
    return $true
}

# Function to display test menu
function Show-TestMenu {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "   MBTI Knowledge Base Quick Tests" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Available test types:" -ForegroundColor White
    Write-Host "  connectivity  - Test basic Knowledge Base connectivity" -ForegroundColor Gray
    Write-Host "  mbti          - Test MBTI personality type queries" -ForegroundColor Gray
    Write-Host "  geographic    - Test geographic filtering" -ForegroundColor Gray
    Write-Host "  performance   - Test response performance" -ForegroundColor Gray
    Write-Host "  all           - Run all tests (default)" -ForegroundColor Gray
    Write-Host ""
}

# Function to run the test
function Invoke-KnowledgeBaseTest {
    param([string]$Type)
    
    Write-Host "🚀 Running Knowledge Base tests (type: $Type)..." -ForegroundColor Green
    Write-Host ""
    
    try {
        # Run the Python test script
        $result = python test_knowledge_base_quick.py $Type
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "✅ Test completed successfully!" -ForegroundColor Green
            return $true
        } else {
            Write-Host ""
            Write-Host "❌ Test execution failed with exit code: $LASTEXITCODE" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Host "❌ Error running test: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Function to show results
function Show-Results {
    Write-Host ""
    Write-Host "📊 Test Results:" -ForegroundColor Cyan
    Write-Host "=================" -ForegroundColor Cyan
    
    # Find latest result files
    $resultFiles = Get-ChildItem -Path "." -Name "*test_results*.json" | Sort-Object LastWriteTime -Descending
    
    if ($resultFiles.Count -gt 0) {
        Write-Host "📄 Latest result files:" -ForegroundColor White
        foreach ($file in $resultFiles | Select-Object -First 3) {
            $fileInfo = Get-Item $file
            Write-Host "   $($file) ($(Get-Date $fileInfo.LastWriteTime -Format 'yyyy-MM-dd HH:mm:ss'))" -ForegroundColor Gray
        }
        
        # Show summary of latest result
        $latestFile = $resultFiles[0]
        try {
            $jsonContent = Get-Content $latestFile | ConvertFrom-Json
            Write-Host ""
            Write-Host "📋 Latest Test Summary:" -ForegroundColor White
            Write-Host "   Status: $($jsonContent.status)" -ForegroundColor Gray
            Write-Host "   Execution Time: $([math]::Round($jsonContent.total_execution_time, 2))s" -ForegroundColor Gray
            Write-Host "   Knowledge Base ID: $($jsonContent.knowledge_base_id)" -ForegroundColor Gray
        }
        catch {
            Write-Host "   Could not parse latest result file" -ForegroundColor Yellow
        }
    } else {
        Write-Host "📄 No test result files found" -ForegroundColor Yellow
    }
}

# Function to show usage examples
function Show-Usage {
    Write-Host ""
    Write-Host "💡 Usage Examples:" -ForegroundColor Cyan
    Write-Host "==================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "# Run all tests (comprehensive)" -ForegroundColor Gray
    Write-Host ".\run_kb_tests.ps1" -ForegroundColor White
    Write-Host ""
    Write-Host "# Test specific functionality" -ForegroundColor Gray
    Write-Host ".\run_kb_tests.ps1 -TestType connectivity" -ForegroundColor White
    Write-Host ".\run_kb_tests.ps1 -TestType mbti" -ForegroundColor White
    Write-Host ".\run_kb_tests.ps1 -TestType geographic" -ForegroundColor White
    Write-Host ".\run_kb_tests.ps1 -TestType performance" -ForegroundColor White
    Write-Host ""
    Write-Host "# Alternative syntax" -ForegroundColor Gray
    Write-Host ".\run_kb_tests.ps1 mbti" -ForegroundColor White
    Write-Host ""
}

# Main execution
function Main {
    # Show header
    Show-TestMenu
    
    # Check prerequisites
    if (-not (Test-Prerequisites)) {
        Write-Host ""
        Write-Host "❌ Prerequisites not met. Please install required components." -ForegroundColor Red
        Show-Usage
        exit 1
    }
    
    Write-Host ""
    Write-Host "🎯 Test Type: $TestType" -ForegroundColor Cyan
    
    # Run the test
    $success = Invoke-KnowledgeBaseTest -Type $TestType
    
    if ($success) {
        Show-Results
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "   All tests completed successfully!" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Red
        Write-Host "   Tests failed. Check output above." -ForegroundColor Red
        Write-Host "========================================" -ForegroundColor Red
        Show-Usage
        exit 1
    }
    
    Write-Host ""
}

# Execute main function
Main