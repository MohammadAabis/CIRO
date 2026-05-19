# Phase 1: Gemini Agent Enablement — Testing Guide

## Current Status

✅ **Done:**

- Verified Gemini API key is configured (`AIzaSyCgM_IOZPnl-_z1Z3AxUkUlbgNEi6mr_P8`)
- Checked `orchestrator.py` has Gemini client initialization with schema-enforced responses
- Updated `.env` to `USE_LIVE_APIS=true`

## Step-by-Step Testing

### 1. Test Gemini API Connectivity

```bash
cd backend
source .venv/Scripts/activate  # On Windows: .venv\Scripts\activate.bat
python test_gemini.py
```

**Expected Output:**

```
GOOGLE_API_KEY configured: True
API Key (first 20 chars): AIzaSyCgM_IOZPnl-_...
GEMINI_MODEL: gemini-flash-latest

✓ Google GenAI client initialized successfully

Test prompt: What is the capital of Pakistan? Respond in one sentence.

✓ Gemini API Response:
The capital of Pakistan is Islamabad.

✅ Gemini API is working correctly!
```

### 2. Start Backend with Live APIs

```bash
cd backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Expected Output:**

```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
INFO:uvicorn.access: "GET /health HTTP/1.1" 200
```

### 3. Check API Health

```bash
curl http://127.0.0.1:8000/health
```

**Expected Response:**

```json
{ "status": "ok" }
```

### 4. Send Test Signal to Trigger Gemini Pipeline

Open **another terminal** and run:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "source": "SOCIAL_MEDIA",
    "raw_text": "EMERGENCY: Heavy rain flooding in G-10 Islamabad. Water level rising rapidly in Sector G-10 market. Reports from social media indicate 50+ people stranded.",
    "location": {
      "latitude": 33.6844,
      "longitude": 73.0479,
      "label": "G-10, Islamabad"
    }
  }'
```

**Expected Response:**

```json
{ "status": "ingested", "signal_id": "<uuid>" }
```

### 5. Monitor Backend Logs for Gemini Processing

In the backend terminal, look for these log messages:

```
Starting orchestration pipeline run <uuid> (Gemini API: True)
INFO: SignalFusionAgent - Fusing 1 active raw signal inputs...
INFO: CrisisClassifier - Classified: <Crisis Title> | Severity: <level>/5
INFO: ResourceAllocator - Allocated units: <list>
INFO: SimulationAgent - Mitigation index: 0.XX
```

### 6. Retrieve Processed Crisis Data

```bash
curl http://127.0.0.1:8000/api/v1/crises
```

**Expected Response:**

```json
{
  "count": 1,
  "crises": [
    {
      "id": "<uuid>",
      "crisis_type": "URBAN_FLOOD",
      "title": "Urban Flooding — G-10 Islamabad",
      "severity": 4,
      "location": {"latitude": 33.6844, "longitude": 73.0479, "label": "G-10, Islamabad"},
      ...
    }
  ]
}
```

### 7. View Trace Log (Agent Reasoning)

```bash
curl http://127.0.0.1:8000/api/v1/traces
```

**Expected:** Full trace of Gemini reasoning with timestamps and step-by-step analysis

### 8. Check Resources Were Allocated

```bash
curl http://127.0.0.1:8000/api/v1/resources
```

**Expected:** Resources marked as `DEPLOYED` for the crisis

## Troubleshooting

| Issue                                                  | Solution                                                          |
| ------------------------------------------------------ | ----------------------------------------------------------------- |
| `ModuleNotFoundError: No module named 'google'`        | Run `pip install -r requirements.txt`                             |
| `Gemini API: False` in logs                            | Verify `USE_LIVE_APIS=true` in `.env` and API key is valid        |
| `ServiceUnavailable` error                             | Check internet connection, Gemini API quota, and API key validity |
| Response shows fallback engine (`"is_fallback": true`) | API key invalid or quota exceeded; falling back to mock           |

## Success Criteria for Phase 1 ✅

- [x] Gemini API client initializes without errors
- [x] Test signal ingestion triggers orchestrator
- [ ] Gemini processes signal (check logs for "Gemini API: True")
- [ ] Crisis classified with Gemini reasoning
- [ ] Resources allocated based on Gemini analysis
- [ ] Trace log shows full agent pipeline execution
- [ ] All responses use real Gemini reasoning (not fallback)

## Next Phase

Once Phase 1 testing passes, proceed to **Phase 2: Integrate Real Data Sources** (OpenWeatherMap, live signals)
