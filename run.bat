@echo off
REM Email Assistant Agent - Quick Start Script (Windows)

echo ==================================
echo Email Assistant Agent - Quick Start
echo ==================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt --quiet

REM Check if .env exists
if not exist ".env" (
    echo.
    echo Warning: .env file not found!
    echo Creating .env from .env.example...
    copy .env.example .env
    echo.
    echo Please edit .env file and add your API keys:
    echo   - OPENAI_API_KEY or ANTHROPIC_API_KEY
    echo.
    pause
)

REM Check if credentials.json exists
if not exist "credentials.json" (
    echo.
    echo Warning: credentials.json not found!
    echo.
    echo Please download credentials.json from Google Cloud Console:
    echo   1. Go to https://console.cloud.google.com/
    echo   2. Enable Gmail API
    echo   3. Create OAuth 2.0 credentials
    echo   4. Download credentials.json to this directory
    echo.
    pause
)

REM Run setup test
echo.
echo Running setup test...
python test_setup.py

if %errorlevel% equ 0 (
    echo.
    echo Setup test passed!
    echo.
    echo Starting Email Assistant Agent...
    echo The app will open in your browser at http://localhost:8501
    echo.
    streamlit run app.py
) else (
    echo.
    echo Setup test failed. Please fix the errors above.
    pause
    exit /b 1
)
