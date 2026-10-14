@echo off
REM Setup script for Explainable RL Ms-Pacman on Windows
REM Run this after cloning the repository

echo ============================================
echo  Explainable RL Ms-Pacman - Setup Script
echo ============================================
echo.

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Please install Python 3.8+
    pause
    exit /b 1
)

echo [1/4] Creating virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

echo [2/4] Upgrading pip...
python -m pip install --upgrade pip setuptools wheel

echo [3/4] Installing dependencies...
pip install -r requirements.txt

echo [4/4] Verifying environment...
python src\environment.py

echo.
echo ============================================
echo  ? Setup complete!
echo ============================================
echo.
echo Next steps:
echo  1. Activate environment: venv\Scripts\activate.bat
echo  2. Train agent: python src\train.py
echo  3. View dashboard: streamlit run src\dashboard.py
echo.
pause
