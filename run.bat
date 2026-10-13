@echo off
:: ╔═══════════════════════════════════════════════════════╗
:: ║       NutriAI — Nutrition Agentic AI Launcher         ║
:: ║       Powered by IBM Granite (watsonx.ai)             ║
:: ╚═══════════════════════════════════════════════════════╝

title NutriAI — IBM Granite Nutrition Agent

color 0B
echo.
echo  ============================================================
echo     NutriAI — Nutrition Agentic AI Application
echo     Powered by IBM Granite LLM via watsonx.ai
echo  ============================================================
echo.

:: ── Step 1: Navigate to the project directory ──────────────
cd /d "%~dp0"
echo [1/5] Project directory: %CD%
echo.

:: ── Step 2: Check Python installation ──────────────────────
echo [2/5] Checking Python...
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo  ERROR: Python is not installed or not in PATH.
    echo  Please install Python 3.9+ from https://www.python.org/downloads/
    echo  Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)
python --version
echo  Python found. OK.
echo.

:: ── Step 3: Create virtual environment (if not exists) ─────
echo [3/5] Setting up virtual environment...
IF NOT EXIST "venv\" (
    echo  Creating virtual environment...
    python -m venv venv
    IF %ERRORLEVEL% NEQ 0 (
        echo  ERROR: Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo  Virtual environment created. OK.
) ELSE (
    echo  Virtual environment already exists. Skipping.
)
echo.

:: ── Step 4: Install dependencies ──────────────────────────
echo [4/5] Installing dependencies...
call venv\Scripts\activate.bat
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
IF %ERRORLEVEL% NEQ 0 (
    echo  ERROR: Failed to install dependencies.
    echo  Check requirements.txt and your internet connection.
    pause
    exit /b 1
)
echo  Dependencies installed. OK.
echo.
echo  NOTE: To use the IBM watsonx.ai Python SDK (optional, faster inference):
echo    pip install ibm-watsonx-ai
echo  (Requires C++ build tools. Without it, REST API fallback is used automatically.)
echo.

:: ── Step 5: Set up .env if not present ────────────────────
IF NOT EXIST ".env" (
    echo  Creating .env from template...
    copy ".env.example" ".env" >nul
    echo.
    echo  ┌─────────────────────────────────────────────────────┐
    echo  │  IMPORTANT: Configure your IBM watsonx.ai API key   │
    echo  │                                                     │
    echo  │  Edit .env and set:                                 │
    echo  │    WATSONX_API_KEY=your_actual_api_key              │
    echo  │    WATSONX_PROJECT_ID=your_project_id               │
    echo  │                                                     │
    echo  │  Get keys from: https://cloud.ibm.com               │
    echo  │                                                     │
    echo  │  Without an API key, the app runs in DEMO mode      │
    echo  │  with realistic mock responses.                     │
    echo  └─────────────────────────────────────────────────────┘
    echo.
)

:: ── Step 6: Create plans output directory ─────────────────
IF NOT EXIST "plans\" (
    mkdir plans
    echo  Created plans\ directory for saving nutrition plans.
)

:: ── Step 7: Start the Flask application ───────────────────
echo [5/5] Starting NutriAI server...
echo.
echo  ┌─────────────────────────────────────────────────────────┐
echo  │  NutriAI is starting...                                 │
echo  │                                                         │
echo  │  Once started, open your browser at:                   │
echo  │  >>> http://localhost:5000 <<<                          │
echo  │                                                         │
echo  │  Press CTRL+C to stop the server.                      │
echo  └─────────────────────────────────────────────────────────┘
echo.

:: Open browser after 3 seconds
start /min "" cmd /c "timeout /t 3 /nobreak >nul && start http://localhost:5000"

:: Run Flask app
python app.py

:: If Flask exits (CTRL+C or error)
echo.
echo  NutriAI server stopped.
pause
