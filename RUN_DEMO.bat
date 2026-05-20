@echo off
REM ================================================================
REM CIRO Flood Scenario Demonstration Script
REM ================================================================
REM This script demonstrates the complete flood response system
REM for the examiner/checker
REM ================================================================

echo.
echo ================================================================
echo  CIRO - FLOOD SCENARIO DEMONSTRATION
echo ================================================================
echo.
echo This script will:
echo  1. Start the backend server with live data
echo  2. Run the flood scenario test
echo  3. Show how the system responds to a detected flood
echo.
echo ================================================================
echo.

REM Navigate to backend
cd /d d:\Projects\CIRO(AntiGravity)\backend

echo Starting Backend Server...
echo (Keep this terminal open and switch to another for the test)
echo.
start cmd /k python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

REM Wait for backend to start
timeout /t 5 /nobreak

echo.
echo ================================================================
echo  Backend is starting... Open another terminal for the test
echo ================================================================
echo.
echo In a new terminal, run:
echo   cd d:\Projects\CIRO(AntiGravity)\backend
echo   python test_flood_scenario.py
echo.
echo Or run the Flutter app:
echo   cd d:\Projects\CIRO(AntiGravity)\frontend
echo   flutter run -d chrome
echo.
pause
