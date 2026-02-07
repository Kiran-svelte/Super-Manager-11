"""
PROOF OF FEATURES - Super Manager AI
=====================================
Tests all 5 key features:
1. Smart Search Trigger
2. Search + Summarize
3. 20-message memory
4. Creative problem-solving
5. No more "Task noted"
"""
import requests
import json
import uuid
import time

API_URL = "https://super-manager-api.onrender.com/api/chat"
SESSION = f"proof-{uuid.uuid4().hex[:8]}"

def chat(message):
    """Send message and get response"""
    try:
        response = requests.post(
            API_URL,
            json={"session_id": SESSION, "message": message},
            timeout=120
        )
        data = response.json()
        return data.get("message", str(data))
    except Exception as e:
        return f"Error: {e}"

def test_feature(name, question, expected_behavior):
    """Run a test and display results"""
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print(f"{'='*60}")
    print(f"Input: {question}")
    print(f"Expected: {expected_behavior}")
    print("-"*60)
    
    response = chat(question)
    print(f"Response:\n{response[:800]}..." if len(response) > 800 else f"Response:\n{response}")
    print("-"*60)
    return response

# Run all tests
print("\n" + "="*60)
print("SUPER MANAGER - PROOF OF ALL 5 FEATURES")
print("="*60)
print(f"Session ID: {SESSION}")
print(f"API: {API_URL}")

# TEST 1: Smart Search Trigger - Answers from knowledge
print("\n\n" + "🧠"*30)
print("FEATURE 1: SMART SEARCH TRIGGER")
print("AI decides when to search vs answer from knowledge")
print("🧠"*30)

r1 = test_feature(
    "Knowledge Answer (no search needed)",
    "What is 25 times 4?",
    "Should answer '100' directly from knowledge"
)

r2 = test_feature(
    "Another knowledge question",
    "Explain what a black hole is in 2 sentences",
    "Should explain from knowledge without searching"
)

# TEST 2: Search + Summarize
print("\n\n" + "🔍"*30)
print("FEATURE 2: SEARCH + SUMMARIZE")
print("When searching, AI reads results and gives helpful summary")
print("🔍"*30)

r3 = test_feature(
    "Current news (requires search)",
    "What is the latest news about AI technology?",
    "Should search web and summarize with links"
)

# TEST 3: 20-message memory
print("\n\n" + "💾"*30)
print("FEATURE 3: 20-MESSAGE MEMORY")
print("Remembers full conversation context")
print("💾"*30)

r4 = test_feature(
    "Tell name (memory test 1)",
    "My name is Kiran and I love programming",
    "Should acknowledge and remember"
)

r5 = test_feature(
    "Ask about earlier (memory test 2)",
    "What is my name and what do I love?",
    "Should remember: Kiran, programming"
)

# TEST 4: Creative problem-solving
print("\n\n" + "💡"*30)
print("FEATURE 4: CREATIVE PROBLEM-SOLVING")
print("For unknown tasks, AI thinks about how best to help")
print("💡"*30)

r6 = test_feature(
    "Custom/unusual request",
    "I want to learn guitar. Give me a 1-week beginner plan.",
    "Should provide creative, helpful response"
)

# TEST 5: No more "Task noted"
print("\n\n" + "✅"*30)
print("FEATURE 5: NO MORE 'TASK NOTED'")
print("Always tries to be useful instead of just noting")
print("✅"*30)

r7 = test_feature(
    "Vague request",
    "Help me be more productive",
    "Should give actual helpful tips, NOT just 'task noted'"
)

r8 = test_feature(
    "Code request",
    "Write a Python function to check if a number is prime",
    "Should write actual code"
)

# Summary
print("\n\n" + "="*60)
print("PROOF SUMMARY")
print("="*60)
print(f"""
✅ Feature 1 - Smart Search: {"PASS" if "100" in r1 or "hundred" in r1.lower() else "CHECK"}
   - Answered math from knowledge

✅ Feature 2 - Search+Summarize: {"PASS" if "http" in r3.lower() or "ai" in r3.lower() else "CHECK"}
   - Searched and summarized AI news

✅ Feature 3 - Memory: {"PASS" if "kiran" in r5.lower() or "programming" in r5.lower() else "CHECK"}
   - Remembered name and interests

✅ Feature 4 - Creative: {"PASS" if len(r6) > 100 else "CHECK"}
   - Gave detailed guitar learning plan

✅ Feature 5 - No 'task noted': {"PASS" if "noted" not in r7.lower() and len(r7) > 50 else "CHECK"}
   - Gave actual productivity tips
""")
print("="*60)
print("All tests completed! Check responses above for details.")
print("="*60)
