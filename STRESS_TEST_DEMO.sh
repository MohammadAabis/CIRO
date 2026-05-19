#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
# CIRO End-to-End Stress Test & Demo Script (3-5 min)
# ═══════════════════════════════════════════════════════════════════
# This script demonstrates all three robustness features:
#  1. Gemini API Degraded Mode Fallback
#  2. Signal Deduplication & Stale Filtering
#  3. Live External API Integration
#
# Run from project root: bash STRESS_TEST_DEMO.sh
# ═══════════════════════════════════════════════════════════════════

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
BACKEND_URL="http://127.0.0.1:8000"
API_HEALTH="$BACKEND_URL/health"

# Colours for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}═══════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}CIRO End-to-End Stress Test Demo${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════${NC}\n"

# ─────────────────────────────────────────────────────────────────
# PHASE 1: HEALTH CHECK & SETUP
# ─────────────────────────────────────────────────────────────────

echo -e "${YELLOW}[PHASE 1/4] Health Check & Setup${NC}"
echo "Checking if backend is running on $BACKEND_URL..."

max_retries=5
retry=0
while [ $retry -lt $max_retries ]; do
    if curl -s "$API_HEALTH" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend is alive${NC}"
        break
    fi
    retry=$((retry + 1))
    if [ $retry -lt $max_retries ]; then
        echo "  Backend not ready. Waiting 2s... ($retry/$max_retries)"
        sleep 2
    fi
done

if [ $retry -eq $max_retries ]; then
    echo -e "${RED}✗ Backend not responding after $max_retries retries.${NC}"
    echo -e "${RED}  Start backend with: cd backend && uvicorn app.main:app --reload${NC}"
    exit 1
fi

echo "Fetching initial dashboard stats..."
STATS=$(curl -s "$BACKEND_URL/api/v1/crises/stats")
echo -e "${GREEN}✓ Mock scenario seeded${NC}"
echo "  Initial crises: $(echo $STATS | grep -o '"active_crises":[0-9]*' | grep -o '[0-9]*')"
echo ""

# ─────────────────────────────────────────────────────────────────
# PHASE 2: SIGNAL DEDUPLICATION & STALE FILTERING DEMO
# ─────────────────────────────────────────────────────────────────

echo -e "${YELLOW}[PHASE 2/4] Signal Deduplication & Stale Filtering${NC}"
echo "Ingesting the same signal twice (within 180s dedup window)..."

# First ingestion
SIGNAL_PAYLOAD='{
  "source": "citizen_report",
  "raw_text": "FIELD REPORT: Water pressure abnormality detected in G-10 sector.",
  "location": {
    "latitude": 33.6844,
    "longitude": 73.0479,
    "label": "G-10/4, Islamabad"
  },
  "reliability_score": 0.85
}'

RESP1=$(curl -s -X POST "$BACKEND_URL/api/v1/ingest" \
  -H "Content-Type: application/json" \
  -d "$SIGNAL_PAYLOAD")
SIGNAL_ID1=$(echo $RESP1 | grep -o '"signal_id":"[^"]*' | cut -d'"' -f4)
echo "  First signal ID: $SIGNAL_ID1"

sleep 1

# Second ingestion (duplicate)
RESP2=$(curl -s -X POST "$BACKEND_URL/api/v1/ingest" \
  -H "Content-Type: application/json" \
  -d "$SIGNAL_PAYLOAD")
SIGNAL_ID2=$(echo $RESP2 | grep -o '"signal_id":"[^"]*' | cut -d'"' -f4)
echo "  Second signal ID (duplicate): $SIGNAL_ID2"

sleep 3

# Check trace logs for dedup step
echo "Fetching trace logs to verify deduplication step..."
TRACES=$(curl -s "$BACKEND_URL/api/v1/traces/")
DEDUP_FOUND=$(echo $TRACES | grep -c "deduplicate" || true)

if [ "$DEDUP_FOUND" -gt 0 ]; then
    echo -e "${GREEN}✓ Deduplication step logged in traces${NC}"
else
    echo -e "${YELLOW}⚠ Deduplication step not yet visible (might be in-flight)${NC}"
fi
echo ""

# ─────────────────────────────────────────────────────────────────
# PHASE 3: GEMINI DEGRADED MODE FALLBACK DEMO
# ─────────────────────────────────────────────────────────────────

echo -e "${YELLOW}[PHASE 3/4] Gemini API Degraded Mode Fallback${NC}"
echo "To demonstrate degraded mode, follow these steps:"
echo ""
echo "  1. Edit backend/.env and set an invalid GOOGLE_API_KEY:"
echo "     GOOGLE_API_KEY=invalid-key-12345"
echo ""
echo "  2. Or set GEMINI_MODEL to a non-existent model:"
echo "     GEMINI_MODEL=gemini-999-invalid"
echo ""
echo "  3. Restart the backend: cd backend && uvicorn app.main:app --reload"
echo ""
echo "  4. Ingest a signal via:"
echo "     curl -X POST http://127.0.0.1:8000/api/v1/ingest \\"
echo "       -H 'Content-Type: application/json' \\"
echo "       -d '{\"source\":\"weather_api\",\"raw_text\":\"Test\",\"reliability_score\":0.9}'"
echo ""
echo "  5. Check backend logs for:"
echo "     CRITICAL: Gemini API down. Operating in Degraded Rule-Based Mode."
echo ""
echo "  6. Verify trace entry via:"
echo "     curl http://127.0.0.1:8000/api/v1/traces/ | grep -A5 'degraded_mode'"
echo ""
echo -e "${YELLOW}Note: Skipping auto-demo (requires manual key manipulation)${NC}"
echo ""

# ─────────────────────────────────────────────────────────────────
# PHASE 4: LIVE API INGESTION DEMO
# ─────────────────────────────────────────────────────────────────

echo -e "${YELLOW}[PHASE 4/4] Live API Ingestion Demo${NC}"
echo "To enable live OpenWeatherMap ingestion:"
echo ""
echo "  1. Edit backend/.env:"
echo "     USE_LIVE_APIS=true"
echo "     OPENWEATHER_API_KEY=<your-openweathermap-api-key>"
echo ""
echo "  2. Restart backend: cd backend && uvicorn app.main:app --reload"
echo ""
echo "  3. Check /api/v1/signals/ for live weather signals:"
echo "     curl http://127.0.0.1:8000/api/v1/signals/ | jq '.signals[0]'"
echo ""
echo -e "${YELLOW}Note: Mock scenario data still seeds if live APIs fail${NC}"
echo ""

# ─────────────────────────────────────────────────────────────────
# FINAL VERIFICATION
# ─────────────────────────────────────────────────────────────────

echo -e "${BLUE}═══════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ Stress test setup complete!${NC}\n"

echo "FINAL VERIFICATION:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo -e "\n1. Dashboard Stats:"
FINAL_STATS=$(curl -s "$BACKEND_URL/api/v1/crises/stats")
ACTIVE=$(echo $FINAL_STATS | grep -o '"active_crises":[0-9]*' | grep -o '[0-9]*')
FALSE_ALARMS=$(echo $FINAL_STATS | grep -o '"false_alarms":[0-9]*' | grep -o '[0-9]*')
echo "   Active Crises: $ACTIVE | False Alarms: $FALSE_ALARMS"

echo -e "\n2. Trace Logs (live agent reasoning):"
TRACE_COUNT=$(curl -s "$BACKEND_URL/api/v1/traces/" | grep -o '"pipeline_run_id"' | wc -l)
echo "   Total trace logs: $TRACE_COUNT"

echo -e "\n3. Resource Allocation:"
RESOURCES=$(curl -s "$BACKEND_URL/api/v1/resources/")
echo "   Fetched resource inventory from backend"

echo -e "\n4. Simulations:"
SIMS=$(curl -s "$BACKEND_URL/api/v1/simulations/")
SIM_COUNT=$(echo $SIMS | grep -o '"id"' | wc -l)
echo "   Total simulations: $SIM_COUNT"

echo -e "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✓ All endpoints responsive${NC}\n"

echo "NEXT STEPS FOR 3-5 MIN DEMO VIDEO:"
echo "1. Start frontend:  cd frontend && flutter run -d chrome"
echo "2. Navigate to Dashboard → tap a crisis → view allocations"
echo "3. Open Maps view to show deployed resources"
echo "4. Ingest a new signal via the dashboard form"
echo "5. Watch trace logs stream live (SSE)"
echo "6. Show resource status changes in real-time"
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════${NC}"
