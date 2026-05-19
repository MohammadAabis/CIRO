#!/usr/bin/env python3
"""
Direct test of Gemini API to diagnose connection issues.
"""
import json
from app.core.config import settings

print("="*60)
print("CIRO Gemini API Diagnostic")
print("="*60)

print(f"\n1. Configuration Check")
print(f"   GOOGLE_API_KEY: {settings.GOOGLE_API_KEY[:30]}...")
print(f"   GEMINI_MODEL: {settings.GEMINI_MODEL}")
print(f"   USE_LIVE_APIS: {settings.USE_LIVE_APIS}")

# Check if we're supposed to use real API
use_real = bool(settings.GOOGLE_API_KEY and "your-gemini" not in settings.GOOGLE_API_KEY.lower())
print(f"\n2. Should Use Real Gemini: {use_real}")

if not use_real:
    print("   ❌ Config check failed - will use fallback")
    exit(1)

# Try to import and initialize client
print(f"\n3. Attempting to import google.genai...")
try:
    from google import genai
    print("   ✅ google.genai imported successfully")
except ImportError as e:
    print(f"   ❌ Failed to import: {e}")
    exit(1)

print(f"\n4. Initializing Gemini client...")
try:
    client = genai.Client(api_key=settings.GOOGLE_API_KEY)
    print("   ✅ Client initialized successfully")
except Exception as e:
    print(f"   ❌ Failed to initialize: {e}")
    exit(1)

print(f"\n5. Testing simple API call...")
try:
    response = client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents="What is 2+2?"
    )
    print(f"   ✅ API call successful!")
    print(f"   Response: {response.text[:100]}")
except Exception as e:
    print(f"   ❌ API call failed: {type(e).__name__}: {e}")
    print(f"\n   Possible causes:")
    print(f"   - Invalid API key")
    print(f"   - Gemini API not enabled in Google Cloud")
    print(f"   - Rate limited")
    print(f"   - Network/connectivity issue")
    exit(1)

print(f"\n6. Testing schema-enforced response...")
try:
    from pydantic import BaseModel, Field
    
    class TestResponse(BaseModel):
        answer: str = Field(..., description="The answer")
        confidence: float = Field(..., description="Confidence 0-1")
    
    response = client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents="Answer: What is the capital of Pakistan?",
        config={
            "response_mime_type": "application/json",
            "response_schema": TestResponse
        }
    )
    result = TestResponse.model_validate_json(response.text)
    print(f"   ✅ Schema-enforced response successful!")
    print(f"   Answer: {result.answer}")
    print(f"   Confidence: {result.confidence}")
except Exception as e:
    print(f"   ❌ Schema-enforced call failed: {type(e).__name__}: {e}")
    exit(1)

print(f"\n{'='*60}")
print("✅ All Gemini API tests passed!")
print("The orchestrator should now use real Gemini (not fallback)")
print(f"{'='*60}\n")
