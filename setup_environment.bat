@echo off
REM GPS Helpers Environment Setup Script for Windows
REM This script sets up a Python virtual environment and installs all dependencies
REM for the GPS helpers tools (GPS Route Manager and GPX Fixer)

setlocal enabledelayedexpansion

echo [INFO] GPS Helpers Environment Setup
echo [INFO] ================================

REM Get the directory where this script is located
set "SCRIPT_DIR=%~dp0"
set "VENV_DIR=%SCRIPT_DIR%venv"
set "REQUIREMENTS_FILE=%SCRIPT_DIR%requirements.txt"

echo [INFO] Script directory: %SCRIPT_DIR%

REM Check if Python is available
echo [INFO] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH
    echo [INFO] Please install Python 3.6 or higher from https://python.org
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [SUCCESS] Python found: !PYTHON_VERSION!

REM Create virtual environment
echo [INFO] Creating virtual environment...
if exist "%VENV_DIR%" (
    echo [WARNING] Virtual environment already exists at %VENV_DIR%
    set /p RECREATE="Do you want to recreate it? (y/N): "
    if /i "!RECREATE!"=="y" (
        echo [INFO] Removing existing virtual environment...
        rmdir /s /q "%VENV_DIR%"
    ) else (
        echo [INFO] Using existing virtual environment
        goto :activate_venv
    )
)

echo [INFO] Creating new virtual environment...
python -m venv "%VENV_DIR%"
if %errorlevel% neq 0 (
    echo [ERROR] Failed to create virtual environment
    pause
    exit /b 1
)
echo [SUCCESS] Virtual environment created successfully

:activate_venv
echo [INFO] Activating virtual environment...
call "%VENV_DIR%\Scripts\activate.bat"
if %errorlevel% neq 0 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)
echo [SUCCESS] Virtual environment activated

REM Update pip
echo [INFO] Updating pip...
python -m pip install --upgrade pip

REM Install dependencies
echo [INFO] Installing dependencies...

REM Create requirements.txt if it doesn't exist
if not exist "%REQUIREMENTS_FILE%" (
    echo [INFO] Creating requirements.txt...
    (
        echo # GPS Helpers Dependencies
        echo gpxpy^>=1.5.0
        echo.
        echo # Optional dependencies for enhanced functionality
        echo # matplotlib^>=3.5.0  # For route visualization ^(uncomment if needed^)
        echo # folium^>=0.12.0     # For interactive maps ^(uncomment if needed^)
    ) > "%REQUIREMENTS_FILE%"
    echo [SUCCESS] Created requirements.txt
)

REM Install from requirements.txt
echo [INFO] Installing packages from requirements.txt...
pip install -r "%REQUIREMENTS_FILE%"
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)
echo [SUCCESS] Dependencies installed successfully

REM Show installed packages
echo [INFO] Installed packages:
pip list | findstr /i "gpxpy"

REM Create necessary directories
echo [INFO] Creating necessary directories...
if not exist "%SCRIPT_DIR%routes" mkdir "%SCRIPT_DIR%routes"
if not exist "%SCRIPT_DIR%routes\original" mkdir "%SCRIPT_DIR%routes\original"
if not exist "%SCRIPT_DIR%routes\lockito" mkdir "%SCRIPT_DIR%routes\lockito"
echo [SUCCESS] Created directories:
echo [INFO]   - routes\original\ # Place your GPX files here
echo [INFO]   - routes\lockito\  # Processed files (auto-created)

REM Create run scripts
echo [INFO] Creating convenience run scripts...

REM Script to run GPS Route Manager
(
    echo @echo off
    echo REM GPS Route Manager Launcher
    echo.
    echo set "SCRIPT_DIR=%%~dp0"
    echo set "VENV_DIR=%%SCRIPT_DIR%%venv"
    echo.
    echo if not exist "%%VENV_DIR%%" ^(
    echo     echo Virtual environment not found. Please run setup_environment.bat first.
    echo     pause
    echo     exit /b 1
    echo ^)
    echo.
    echo echo Starting GPS Route Manager...
    echo call "%%VENV_DIR%%\Scripts\activate.bat"
    echo python "%%SCRIPT_DIR%%gps_route_manager.py"
    echo pause
) > "%SCRIPT_DIR%run_gui.bat"

REM Script to run GPX Fixer
(
    echo @echo off
    echo REM GPX Fixer Launcher
    echo.
    echo set "SCRIPT_DIR=%%~dp0"
    echo set "VENV_DIR=%%SCRIPT_DIR%%venv"
    echo.
    echo if not exist "%%VENV_DIR%%" ^(
    echo     echo Virtual environment not found. Please run setup_environment.bat first.
    echo     pause
    echo     exit /b 1
    echo ^)
    echo.
    echo echo Starting GPX Fixer...
    echo call "%%VENV_DIR%%\Scripts\activate.bat"
    echo python "%%SCRIPT_DIR%%gpx_fix.py" %%*
    echo pause
) > "%SCRIPT_DIR%run_fixer.bat"

REM Script to activate environment for manual use
(
    echo @echo off
    echo REM Activate GPS Helpers Environment
    echo.
    echo set "SCRIPT_DIR=%%~dp0"
    echo set "VENV_DIR=%%SCRIPT_DIR%%venv"
    echo.
    echo if not exist "%%VENV_DIR%%" ^(
    echo     echo Virtual environment not found. Please run setup_environment.bat first.
    echo     pause
    echo     exit /b 1
    echo ^)
    echo.
    echo echo Activating GPS Helpers environment...
    echo call "%%VENV_DIR%%\Scripts\activate.bat"
    echo echo.
    echo echo Environment activated! You can now run:
    echo echo   python gps_route_manager.py  # Start GUI
    echo echo   python gpx_fix.py [options]  # Run GPX fixer
    echo echo   deactivate                   # Exit environment
    echo echo.
    echo cmd /k
) > "%SCRIPT_DIR%activate_env.bat"

echo [SUCCESS] Created convenience scripts:
echo [INFO]   - run_gui.bat      # Launch GPS Route Manager
echo [INFO]   - run_fixer.bat    # Launch GPX Fixer with arguments
echo [INFO]   - activate_env.bat # Activate environment for manual use

echo.
echo [SUCCESS] Setup completed successfully!
echo.
echo [INFO] You can now use the GPS helpers in several ways:
echo.
echo [INFO] 1. Quick start with convenience scripts:
echo [INFO]    run_gui.bat                    # Start GUI application
echo [INFO]    run_fixer.bat --profile car    # Run GPX fixer
echo.
echo [INFO] 2. Manual activation:
echo [INFO]    activate_env.bat               # Activate environment
echo [INFO]    python gps_route_manager.py   # Start GUI
echo [INFO]    python gpx_fix.py [options]    # Run fixer
echo [INFO]    deactivate                     # Exit environment
echo.
echo [INFO] 3. Direct activation:
echo [INFO]    venv\Scripts\activate.bat     # Activate manually
echo [INFO]    python gps_route_manager.py   # Start GUI
echo [INFO]    python gpx_fix.py [options]    # Run fixer
echo.
echo [INFO] Next steps:
echo [INFO] 1. Place your GPX files in the 'routes\original' directory
echo [INFO] 2. Run 'run_gui.bat' to start the GUI application
echo [INFO] 3. Or run 'run_fixer.bat --profile car' for command-line processing
echo.
echo [SUCCESS] Happy GPS route processing!
echo.
pause
