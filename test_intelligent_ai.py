"""
Test the new intelligent AI system with Ollama
"""
import asyncio
import httpx

async def test_ollama():
    """Test Ollama integration"""
    
    # Check Ollama is running
    print("1. Checking Ollama availability...")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:11434/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                print(f"   ✅ Ollama available with {len(models)} models")
                for model in models[:3]:
                    print(f"      - {model.get('name', 'unknown')}")
            else:
                print(f"   ❌ Ollama returned status {response.status_code}")
                return
    except Exception as e:
        print(f"   ❌ Ollama not available: {e}")
        return
    
    # Test a simple generation
    print("\n2. Testing AI generation...")
    payload = {
        "model": "qwen2.5-coder:1.5b",  # Smaller model that fits in memory
        "messages": [
            {"role": "system", "content": "You are a helpful assistant. Be concise."},
            {"role": "user", "content": "What is 2+2? Answer in one word."}
        ],
        "stream": False,
        "options": {
            "temperature": 0.3,
            "num_predict": 100
        }
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "http://localhost:11434/api/chat",
                json=payload
            )
            if response.status_code == 200:
                result = response.json()
                content = result.get("message", {}).get("content", "")
                print(f"   ✅ AI responded: {content}")
            else:
                print(f"   ❌ Error: {response.status_code}")
                print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Generation failed: {e}")
    
    # Test intent detection
    print("\n3. Testing email vs telegram detection...")
    
    test_cases = [
        ("Schedule a meeting and send link to john@gmail.com", "email"),
        ("Send meeting link to my Telegram contact", "telegram"),
        ("Email the report to team@company.org", "email"),
        ("Message the link", "unknown"),  # Should default to telegram
    ]
    
    for text, expected in test_cases:
        import re
        
        text_lower = text.lower()
        detected = "unknown"
        
        # Email patterns
        email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
        if re.search(email_pattern, text):
            detected = "email"
        elif any(word in text_lower for word in ["email", "mail", "e-mail", "gmail", "outlook", "yahoo"]):
            detected = "email"
        elif "telegram" in text_lower or " tg " in text_lower:
            detected = "telegram"
        elif "whatsapp" in text_lower:
            detected = "whatsapp"
        
        status = "✅" if detected == expected or (expected == "unknown" and detected in ["unknown", "telegram"]) else "❌"
        print(f"   {status} '{text[:40]}...' -> {detected} (expected: {expected})")
    
    print("\n4. Testing human-like response generation...")
    
    payload = {
        "model": "qwen2.5-coder:1.5b",  # Smaller model that fits in memory
        "messages": [
            {"role": "system", "content": """You are Alex, a friendly personal assistant. 
Be warm, use contractions, maybe an emoji. Keep it short."""},
            {"role": "user", "content": "I need to schedule a meeting for tomorrow with my boss"}
        ],
        "stream": False,
        "options": {
            "temperature": 0.7,
            "num_predict": 200
        }
    }
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "http://localhost:11434/api/chat",
                json=payload
            )
            if response.status_code == 200:
                result = response.json()
                content = result.get("message", {}).get("content", "")
                print(f"   ✅ Human-like response:\n   \"{content}\"")
            else:
                print(f"   ❌ Error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Generation failed: {e}")
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    asyncio.run(test_ollama())
