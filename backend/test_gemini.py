#!/usr/bin/env python3
"""
Quick test to verify Gemini API is working with the configured key.
"""
import json
from app.core.config import settings

def test_gemini_api():
    """Test basic Gemini API connectivity."""
    print(f"GOOGLE_API_KEY configured: {bool(settings.GOOGLE_API_KEY)}")
    print(f"API Key (first 20 chars): {settings.GOOGLE_API_KEY[:20]}...")
    print(f"GEMINI_MODEL: {settings.GEMINI_MODEL}")
    
    try:
        from google import genai
        client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        print("\n✓ Google GenAI client initialized successfully\n")
        
        # Simple test prompt
        test_prompt = "What is the capital of Pakistan? Respond in one sentence."
        print(f"Test prompt: {test_prompt}")
        
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=test_prompt
        )
        
        print(f"\n✓ Gemini API Response:\n{response.text}\n")
        print("✅ Gemini API is working correctly!")
        
    except Exception as e:
        print(f"\n❌ Error testing Gemini API:\n{e}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_gemini_api()
    exit(0 if success else 1)
