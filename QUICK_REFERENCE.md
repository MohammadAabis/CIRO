# CIRO Stress Test Quick Reference Card

## 30-Second Checklist

- ✅ Backend running on `http://127.0.0.1:8000`
- ✅ `.env` has valid/invalid `GOOGLE_API_KEY` (fallback works either way)
- ✅ `SIGNAL_DEDUP_WINDOW_SECONDS=180`
- ✅ `SIGNAL_MAX_AGE_MINUTES=120`
- ✅ Frontend ready on `http://127.0.0.1:3000` or `flutter run -d chrome`

---

## Feature 1: Signal Dedup (1:30 min)

```bash
# Terminal 1: Backend
cd backend && uvicorn app.main:app --reload

# Terminal 2: Ingest signal twice
curl -X POST http://127.0.0.1:8000/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{"source":"weather_api","raw_text":"Rainfall 80mm G-10","location":{"latitude":33.6844,"longitude":73.0479,"label":"G-10"},"reliability_score":0.95}'

sleep 1

# Same signal again
curl -X POST http://127.0.0.1:8000/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{"source":"weather_api","raw_text":"Rainfall 80mm G-10","location":{"latitude":33.6844,"longitude":73.0479,"label":"G-10"},"reliability_score":0.95}'

# Terminal 3: Check traces
curl http://127.0.0.1:8000/api/v1/traces/ | jq '.traces[0].entries[-1]'
# Look for: "Dropped 1 duplicates and 0 stale signals. 1 retained."
```

**Proof:** Trace entry shows duplicate was dropped; signal fusion only processes 1 signal, not 2.

---

## Feature 2: Gemini Fallback (1:15 min)

```bash
# Edit backend/.env
# GOOGLE_API_KEY=invalid-key-12345

# Restart backend
cd backend && uvicorn app.main:app --reload

# Watch console for:
# CRITICAL: Gemini API down. Operating in Degraded Rule-Based Mode.

# Ingest a signal
curl -X POST http://127.0.0.1:8000/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{"source":"weather_api","raw_text":"Heatwave 47C F-8","location":{"latitude":33.7060,"longitude":73.0551,"label":"F-8"},"reliability_score":0.9}'

# Check crisis was created
curl http://127.0.0.1:8000/api/v1/crises/ | jq '.crises[0].title'
# Output: "Extreme Heatwave — F-8 Islamabad" (from rule-based fallback)

# Check trace shows degraded_mode step
curl http://127.0.0.1:8000/api/v1/traces/ | jq '.traces[] | select(.crisis_id) | .entries[] | select(.action == "degraded_mode")'
```

**Proof:** System doesn't crash; crisis created successfully; fallback visible in traces.

---

## Feature 3: Live API Toggle (1:15 min)

```bash
# Get OpenWeatherMap key: https://openweathermap.org/api

# Edit backend/.env
# USE_LIVE_APIS=true
# OPENWEATHER_API_KEY=your-key-here

# Restart backend
cd backend && uvicorn app.main:app --reload

# Check console for:
# [CIRO] Live ingestion seeded 1 signal(s).

# Fetch signal (should have live weather data)
curl http://127.0.0.1:8000/api/v1/signals/?limit=1 | jq '.signals[0] | {source, weather}'
# Output includes real temp, humidity, rainfall from Islamabad

# Toggle back to mock
# Edit .env: USE_LIVE_APIS=false
# Restart → mock scenario seeds again
```

**Proof:** Signals differ between live and mock; real-time weather data in signal.

---

## Feature 4: Frontend Integration (2:00 min)

```bash
# Terminal 1: Backend
cd backend && uvicorn app.main:app --reload

# Terminal 2: Frontend
cd frontend && flutter run -d chrome

# Dashboard loads → Show:
# 1. Active crises = 3 (flood, heatwave, false alarm)
# 2. Tap "Urban Flooding — G-10" → detail page
# 3. View "Resources Allocated" section
# 4. Tap map icon → see deployed ambulances/police
# 5. Fill "Ingest New Signal" form → Submit
# 6. Watch trace stream update in real-time (SSE)
```

**Proof:** Dashboard shows live data; trace logs stream in real-time; no crashes.

---

## HTTP Curl Templates

### Ingest Signal (Dedup Test)

```bash
curl -X POST http://127.0.0.1:8000/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "source": "citizen_report",
    "raw_text": "DUPLICATE TEST",
    "location": {"latitude": 33.6844, "longitude": 73.0479, "label": "G-10"},
    "reliability_score": 0.9
  }'
```

### Get Traces

```bash
curl http://127.0.0.1:8000/api/v1/traces/ | jq '.traces[0].entries'
```

### Get Crises Stats

```bash
curl http://127.0.0.1:8000/api/v1/crises/stats | jq '{active_crises, false_alarms, total_signals}'
```

### Get Latest Crisis

```bash
curl http://127.0.0.1:8000/api/v1/crises/ | jq '.crises[0] | {title, severity, confidence, is_false_alarm}'
```

---

## Environment Variables (.env)

```env
# Robustness Features
USE_LIVE_APIS=false
SIGNAL_DEDUP_WINDOW_SECONDS=180
SIGNAL_MAX_AGE_MINUTES=120

# Gemini (can be invalid for fallback demo)
GOOGLE_API_KEY=your-key-or-invalid
GEMINI_MODEL=gemini-2.0-flash

# Live Weather (optional)
OPENWEATHER_API_KEY=
LIVE_WEATHER_LAT=33.6844
LIVE_WEATHER_LON=73.0479
LIVE_WEATHER_LABEL=Islamabad
```

---

## Evaluation Proof Points

| Feature         | Evidence                                    | Demo Time |
| --------------- | ------------------------------------------- | --------- |
| Signal Dedup    | Trace: `"Dropped X duplicates"`             | 1:30      |
| Gemini Fallback | Console: `"CRITICAL: ... Degraded Mode"`    | 1:15      |
| Live API        | Different signals with `USE_LIVE_APIS=true` | 1:15      |
| Error Handling  | 422/500 responses on bad input              | implicit  |
| Frontend        | Dashboard loads + streams traces            | 2:00      |
| **Total**       | —                                           | **5:00**  |

---

## Troubleshooting

| Issue                  | Fix                                |
| ---------------------- | ---------------------------------- |
| Backend won't start    | `pip install -r requirements.txt`  |
| Frontend can't connect | Update `api_client.dart` base URL  |
| Dedup not showing      | Wait 3s after ingest; check traces |
| Fallback not triggered | Restart backend after .env change  |
| Live weather missing   | Set `OPENWEATHER_API_KEY`          |

---

**Built for Anti Gravity Hackathon 🚀**
