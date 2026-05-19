#!/usr/bin/env python3
"""
Send test signal to CIRO backend to trigger Gemini agent pipeline.
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000/api/v1"

# Test signal 1: Heatwave (use lowercase enums)
heatwave_signal = {
    "source": "weather_api",
    "raw_text": "Extreme heatwave alert for F-8. Temperature reached 47C (heat index 52C). High risk of heat strokes. Multiple hyperthermia cases reported.",
    "location": {
        "latitude": 33.7060,
        "longitude": 73.0551,
        "label": "F-8, Islamabad"
    }
}

# Test signal 2: Urban Flood (use lowercase enums)
flood_signal = {
    "source": "social_media",
    "raw_text": "EMERGENCY: Heavy rain flooding in G-10 Islamabad. Water level rising rapidly in Sector G-10 market. Reports indicate 50+ people stranded.",
    "location": {
        "latitude": 33.6844,
        "longitude": 73.0479,
        "label": "G-10, Islamabad"
    }
}

def send_signal(signal, name):
    """Send signal to backend and print response."""
    print(f"\n{'='*60}")
    print(f"Sending: {name}")
    print(f"{'='*60}")
    print(f"Signal: {json.dumps(signal, indent=2)}\n")
    
    try:
        response = requests.post(
            f"{BASE_URL}/ingest",
            json=signal,
            headers={"Content-Type": "application/json"}
        )
        print(f"Response Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}\n")
        return response.json()
    except Exception as e:
        print(f"ERROR: {e}\n")
        return None

def check_crises():
    """Retrieve all crises."""
    print(f"\n{'='*60}")
    print("Current Crises")
    print(f"{'='*60}")
    try:
        response = requests.get(f"{BASE_URL}/crises")
        data = response.json()
        print(f"Total Crises: {data.get('count', 0)}\n")
        for crisis in data.get("crises", []):
            print(f"  ID: {crisis['id']}")
            print(f"  Type: {crisis['crisis_type']}")
            print(f"  Title: {crisis['title']}")
            print(f"  Severity: {crisis['severity']}/5")
            print(f"  Location: {crisis['location']['label']}")
            print()
    except Exception as e:
        print(f"ERROR: {e}\n")

def check_traces():
    """Retrieve trace logs to see agent reasoning."""
    print(f"\n{'='*60}")
    print("Agent Reasoning Traces")
    print(f"{'='*60}")
    try:
        response = requests.get(f"{BASE_URL}/traces")
        data = response.json()
        traces = data.get("traces", [])
        print(f"Total Traces: {len(traces)}\n")
        
        for trace in traces[-3:]:  # Show last 3
            print(f"Pipeline ID: {trace['pipeline_run_id']}")
            entries = trace.get("entries", [])
            for entry in entries:
                print(f"  {entry['agent_name']} ({entry['action']})")
                print(f"    Input: {entry['input_summary'][:80]}...")
                print(f"    Output: {entry['output_summary'][:80]}...")
                print(f"    Duration: {entry['duration_ms']}ms")
                if entry.get('metadata', {}).get('is_fallback'):
                    print(f"    ⚠️  FALLBACK MODE (not using real Gemini)")
                print()
    except Exception as e:
        print(f"ERROR: {e}\n")

if __name__ == "__main__":
    print("CIRO Signal Test Client")
    print("Sending signals to trigger Gemini agent pipeline...\n")
    
    # Send test signals
    send_signal(heatwave_signal, "Heatwave (F-8)")
    send_signal(flood_signal, "Urban Flood (G-10)")
    
    # Wait a bit for processing
    import time
    print("⏳ Waiting 3 seconds for agent pipeline to process...\n")
    time.sleep(3)
    
    # Check results
    check_crises()
    check_traces()
    
    print(f"\n{'='*60}")
    print("✅ Test complete! Check logs above for agent reasoning.")
    print(f"{'='*60}\n")
