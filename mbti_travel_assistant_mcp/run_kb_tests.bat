@echo off
REM Quick Knowledge Base Testing Batch Script
REM Usage: run_kb_tests.bat [test_type]
REM Test types: connectivity, mbti, geographic, performance, all (default)

echo.
echo ========================================
echo   MBTI Knowledge Base Quick Tests
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python and try again
    pause
    exit /b 1
)

REM Check if boto3 is available
python -c "import boto3" >nul 2>&1
if errorlevel 1 (
    echo ERROR: boto3 is not installed
    echo Please install boto3: pip install boto3
    pause
    exit /b 1
)

REM Check AWS credentials
echo Checking AWS credentials...
aws sts get-caller-identity >nul 2>&1
if errorlevel 1 (
    echo WARNING: AWS credentials not configured or AWS CLI not available
    echo Tests may fail without proper AWS credentials
    echo.
)

REM Set test type (default to 'all' if no argument provided)
set TEST_TYPE=%1
if "%TEST_TYPE%"=="" set TEST_TYPE=all

echo Running Knowledge Base tests (type: %TEST_TYPE%)...
echo.

REM Run the test
python test_knowledge_base_quick.py %TEST_TYPE%

if errorlevel 1 (
    echo.
    echo ERROR: Test execution failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Test completed successfully!
echo ========================================
echo.

REM Show available test files
echo Available test files:
dir /b *test_results*.json 2>nul
if errorlevel 1 (
    echo No test result files found
) else (
    echo.
    echo Latest results:
    for /f %%i in ('dir /b /o-d *test_results*.json 2^>nul') do (
        echo   %%i
        goto :found
    )
    :found
)

echo.
echo Available commands:
echo   run_kb_tests.bat connectivity  - Test basic connectivity
echo   run_kb_tests.bat mbti          - Test MBTI personality queries
echo   run_kb_tests.bat geographic    - Test geographic filtering
echo   run_kb_tests.bat performance   - Test response performance
echo   run_kb_tests.bat all           - Run all tests (default)
echo.

pause