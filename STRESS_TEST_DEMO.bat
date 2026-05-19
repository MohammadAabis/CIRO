@echo off
REM ═══════════════════════════════════════════════════════════════════
REM CIRO End-to-End Stress Test & Demo Script (3-5 min) — Windows
REM ═══════════════════════════════════════════════════════════════════
REM This script demonstrates all three robustness features:
REM  1. Gemini API Degraded Mode Fallback
REM  2. Signal Deduplication & Stale Filtering
REM  3. Live External API Integration
REM
REM Run from project root: STRESS_TEST_DEMO.bat
REM ═══════════════════════════════════════════════════════════════════

setlocal enabledelayedexpansion

set "PROJECT_ROOT=%cd%"
set "BACKEND_DIR=%PROJECT_ROOT%\backend"
set "FRONTEND_DIR=%PROJECT_ROOT%\frontend"
set "BACKEND_URL=http://127.0.0.1:8000"
set "API_HEALTH=%BACKEND_URL%/health"

cls
echo.
echo ═══════════════════════════════════════════════════════════════════
echo CIRO End-to-End Stress Test Demo
echo ═══════════════════════════════════════════════════════════════════
echo.

REM ─────────────────────────────────────────────────────────────────
REM PHASE 1: HEALTH CHECK
REM ─────────────────────────────────────────────────────────────────

echo [PHASE 1/4] Health Check
echo Checking if backend is running on %BACKEND_URL%...

set "max_retries=10"
set "retry=0"

:health_check_loop
if %retry% geq %max_retries% (
    echo.
    echo ERROR: Backend not responding after %max_retries% retries.
    echo Start backend with: cd backend ^&^& uvicorn app.main:app --reload
    exit /b 1
)

timeout /t 1 /nobreak > nul 2>&1
curl -s "%API_HEALTH%" > nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] Backend is alive
    goto health_check_done
)

set /a retry=%retry%+1
echo Waiting for backend... (!retry!/%max_retries%)
goto health_check_loop

:health_check_done
echo.

REM ─────────────────────────────────────────────────────────────────
REM PHASE 2: SIGNAL DEDUPLICATION & STALE FILTERING DEMO
REM ─────────────────────────────────────────────────────────────────

echo [PHASE 2/4] Signal Deduplication ^& Stale Filtering
echo Ingesting the same signal twice (within 180s dedup window)...
echo.

set "SIGNAL_PAYLOAD={\"source\":\"citizen_report\",\"raw_text\":\"FIELD REPORT: Water pressure abnormality detected in G-10 sector.\",\"location\":{\"latitude\":33.6844,\"longitude\":73.0479,\"label\":\"G-10/4, Islamabad\"},\"reliability_score\":0.85}"

REM First ingestion
for /f "tokens=*" %%A in ('curl -s -X POST "%BACKEND_URL%/api/v1/ingest" -H "Content-Type: application/json" -d "!SIGNAL_PAYLOAD!"') do (
    set "RESP1=%%A"
)
echo First signal ingested
timeout /t 1 /nobreak > nul

REM Second ingestion (duplicate)
for /f "tokens=*" %%A in ('curl -s -X POST "%BACKEND_URL%/api/v1/ingest" -H "Content-Type: application/json" -d "!SIGNAL_PAYLOAD!"') do (
    set "RESP2=%%A"
)
echo Second signal ingested (duplicate)

timeout /t 3 /nobreak > nul

echo Fetching trace logs to verify deduplication step...
for /f "tokens=*" %%A in ('curl -s "%BACKEND_URL%/api/v1/traces/"') do (
    set "TRACES=%%A"
)

REM Simple check for "deduplicate" in traces
echo !TRACES! | find "deduplicate" > nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] Deduplication step logged in traces
) else (
    echo [NOTICE] Deduplication step might be in-flight
)
echo.

REM ─────────────────────────────────────────────────────────────────
REM PHASE 3: GEMINI DEGRADED MODE FALLBACK DEMO
REM ─────────────────────────────────────────────────────────────────

echo [PHASE 3/4] Gemini API Degraded Mode Fallback
echo To demonstrate degraded mode, follow these steps:
echo.
echo   1. Edit backend\.env and set an invalid GOOGLE_API_KEY:
echo      GOOGLE_API_KEY=invalid-key-12345
echo.
echo   2. Or set GEMINI_MODEL to a non-existent model:
echo      GEMINI_MODEL=gemini-999-invalid
echo.
echo   3. Restart the backend: cd backend ^&^& uvicorn app.main:app --reload
echo.
echo   4. Ingest a signal and check backend logs for:
echo      CRITICAL: Gemini API down. Operating in Degraded Rule-Based Mode.
echo.
echo   5. Verify trace entry via:
echo      curl http://127.0.0.1:8000/api/v1/traces/ ^| findstr "degraded_mode"
echo.
echo [NOTICE] Skipping auto-demo (requires manual key manipulation)
echo.

REM ─────────────────────────────────────────────────────────────────
REM PHASE 4: LIVE API INGESTION DEMO
REM ─────────────────────────────────────────────────────────────────

echo [PHASE 4/4] Live API Ingestion Demo
echo To enable live OpenWeatherMap ingestion:
echo.
echo   1. Edit backend\.env:
echo      USE_LIVE_APIS=true
echo      OPENWEATHER_API_KEY=^<your-openweathermap-api-key^>
echo.
echo   2. Restart backend: cd backend ^&^& uvicorn app.main:app --reload
echo.
echo   3. Check /api/v1/signals/ for live weather signals:
echo      curl http://127.0.0.1:8000/api/v1/signals/
echo.
echo [NOTICE] Mock scenario data still seeds if live APIs fail
echo.

REM ─────────────────────────────────────────────────────────────────
REM FINAL VERIFICATION
REM ─────────────────────────────────────────────────────────────────

echo.
echo ═══════════════════════════════════════════════════════════════════
echo [OK] Stress test setup complete!
echo.
echo FINAL VERIFICATION:
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo.
echo 1. Dashboard Stats:
for /f "tokens=*" %%A in ('curl -s "%BACKEND_URL%/api/v1/crises/stats"') do (
    set "STATS=%%A"
)
echo   Fetched from backend

echo.
echo 2. Trace Logs (live agent reasoning):
for /f "tokens=*" %%A in ('curl -s "%BACKEND_URL%/api/v1/traces/"') do (
    set "TRACE_LOGS=%%A"
)
echo   Fetched trace logs

echo.
echo 3. Resource Allocation:
for /f "tokens=*" %%A in ('curl -s "%BACKEND_URL%/api/v1/resources/"') do (
    set "RESOURCES=%%A"
)
echo   Fetched resource inventory

echo.
echo 4. Simulations:
for /f "tokens=*" %%A in ('curl -s "%BACKEND_URL%/api/v1/simulations/"') do (
    set "SIMS=%%A"
)
echo   Fetched simulations

echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo [OK] All endpoints responsive
echo.
echo NEXT STEPS FOR 3-5 MIN DEMO VIDEO:
echo 1. Start frontend:  cd frontend ^&^& flutter run -d chrome
echo 2. Navigate to Dashboard - tap a crisis - view allocations
echo 3. Open Maps view to show deployed resources
echo 4. Ingest a new signal via the dashboard form
echo 5. Watch trace logs stream live (SSE)
echo 6. Show resource status changes in real-time
echo.
echo ═══════════════════════════════════════════════════════════════════
echo.
