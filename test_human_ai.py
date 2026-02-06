"""
Test the truly human-like AI system

This tests:
1. Groq free tier API connection
2. Emotional state detection
3. Human-like responses
4. Common sense reasoning
"""
import asyncio
import os

# Set up test Groq API key if not set
# GET YOUR FREE KEY FROM: https://console.groq.com/keys
if not os.getenv("GROQ_API_KEY"):
    print("\n" + "="*60)
    print("⚠️  GROQ_API_KEY not set!")
    print("="*60)
    print("\nTo get a FREE Groq API key:")
    print("1. Go to: https://console.groq.com/keys")
    print("2. Sign up/login (FREE)")
    print("3. Click 'Create API Key'")
    print("4. Set it in your .env file:")
    print("   GROQ_API_KEY=gsk_your_key_here")
    print("\nGroq offers FREE tier with:")
    print("- 30 requests per minute")
    print("- 14,400 requests per day") 
    print("- Access to llama-3.3-70b-versatile")
    print("="*60 + "\n")


async def test_groq_connection():
    """Test if Groq API is working"""
    import httpx
    
    api_key = os.getenv("GROQ_API_KEY", "")
    
    print("\n1. Testing Groq API connection...")
    
    if not api_key:
        print("   ❌ No GROQ_API_KEY set - will use Ollama fallback")
        return False
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "user", "content": "Say 'hello' in one word"}],
                    "max_tokens": 10
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                print(f"   ✅ Groq API working! Response: {content}")
                return True
            else:
                print(f"   ❌ Groq API error: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                return False
                
    except Exception as e:
        print(f"   ❌ Groq connection failed: {e}")
        return False


async def test_human_ai():
    """Test the human-like AI system"""
    
    # Import after setting environment
    from backend.core.human_ai import HumanAIManager, Emotion
    
    print("\n2. Testing Human AI Manager...")
    
    ai = HumanAIManager()
    
    # Test emotional detection
    print("\n   Testing emotional state detection:")
    test_inputs = [
        ("Help! I need this urgently!", Emotion.CONCERNED),
        ("Thanks so much, you're amazing!", Emotion.HAPPY),
        ("Let's celebrate my birthday!", Emotion.EXCITED),
        ("I'm feeling stressed about work", Emotion.SYMPATHETIC),
    ]
    
    for user_input, expected_emotion in test_inputs:
        ai._update_emotional_state(user_input)
        actual = ai.emotional_state.primary_emotion
        status = "✅" if actual == expected_emotion else "❌"
        print(f"   {status} '{user_input[:35]}...' -> {actual.value}")
    
    # Test real-world constraint extraction  
    print("\n   Testing constraint extraction:")
    constraints = ai._extract_real_world_constraints(
        "Schedule a meeting for tomorrow with john@gmail.com, budget is tight"
    )
    print(f"   Extracted: {constraints}")
    
    # Test actual AI response
    print("\n3. Testing AI response generation...")
    
    response = await ai.generate_response(
        "I need to schedule a meeting with sarah@company.com for tomorrow afternoon"
    )
    
    print(f"\n   AI Response:\n   {'-'*50}")
    print(f"   {response[:500]}")
    print(f"   {'-'*50}")
    
    # Check response quality
    quality_checks = []
    response_lower = response.lower()
    
    if any(c in response for c in ["?", "!"]):
        quality_checks.append("✅ Natural punctuation")
    if any(word in response_lower for word in ["i'd", "i'll", "you're", "that's", "let's"]):
        quality_checks.append("✅ Uses contractions")
    if len(response) > 50:
        quality_checks.append("✅ Substantive response")
    if "sarah" in response_lower or "tomorrow" in response_lower or "email" in response_lower:
        quality_checks.append("✅ Context-aware")
        
    print(f"\n   Quality checks:")
    for check in quality_checks:
        print(f"   {check}")


async def test_json_generation():
    """Test structured JSON output"""
    
    from backend.core.human_ai import HumanAIManager
    
    print("\n4. Testing JSON task matching...")
    
    ai = HumanAIManager()
    
    result = await ai.generate_response(
        user_input="""Match this user request to a task:
User said: "I want to book a flight to Paris next month"

Return JSON with task_id, confidence, and extracted_info.""",
        json_mode=True
    )
    
    print(f"   Result type: {type(result)}")
    if isinstance(result, dict):
        print(f"   ✅ Got structured JSON: {result}")
    else:
        print(f"   ❌ Expected dict, got: {result[:200] if isinstance(result, str) else result}")


async def main():
    print("="*60)
    print("   HUMAN-LIKE AI SYSTEM TEST")
    print("="*60)
    
    # Test Groq first
    groq_works = await test_groq_connection()
    
    if not groq_works:
        print("\n   ℹ️  Will use Ollama as fallback")
    
    # Test the AI system
    await test_human_ai()
    
    # Test JSON generation
    await test_json_generation()
    
    print("\n" + "="*60)
    print("   TESTS COMPLETE")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
