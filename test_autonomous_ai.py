"""
Test the Autonomous AI System
Tests various capabilities: chat, payments, meetings, reminders
"""
import httpx
import asyncio
import json

# API Base URL
API_BASE = "https://super-manager-api.onrender.com/api/ai"
# For local testing:
# API_BASE = "http://localhost:8000/api/ai"


async def test_autonomous_ai():
    """Test the autonomous AI with various requests"""
    async with httpx.AsyncClient(timeout=60.0) as client:
        print("=" * 60)
        print("  TESTING AUTONOMOUS AI")
        print("=" * 60)
        
        # Test 1: Simple chat
        print("\n[Test 1] Simple greeting...")
        try:
            response = await client.post(f"{API_BASE}/chat", json={
                "message": "Hello! What can you help me with?"
            })
            data = response.json()
            print(f"Response: {data.get('message', data)[:200]}...")
            print(f"Action: {data.get('action')}")
        except Exception as e:
            print(f"Error: {e}")
        
        # Test 2: Meeting scheduling
        print("\n[Test 2] Schedule a meeting...")
        try:
            response = await client.post(f"{API_BASE}/chat", json={
                "message": "Schedule a meeting with john@test.com tomorrow at 3pm about project review"
            })
            data = response.json()
            session_id = data.get('session_id')
            print(f"Response: {data.get('message', data)[:200]}...")
            print(f"Action: {data.get('action')}")
            
            # If it needs confirmation, confirm it
            if data.get('action') == 'confirm' or data.get('requires_confirmation'):
                print("  -> Confirming action...")
                confirm_response = await client.post(f"{API_BASE}/confirm", json={
                    "session_id": session_id,
                    "confirmed": True
                })
                confirm_data = confirm_response.json()
                print(f"  -> Result: {confirm_data.get('message', confirm_data)[:200]}...")
        except Exception as e:
            print(f"Error: {e}")
        
        # Test 3: Payment request
        print("\n[Test 3] Payment request...")
        try:
            response = await client.post(f"{API_BASE}/chat", json={
                "message": "I need to pay ₹500 to friend@upi"
            })
            data = response.json()
            session_id = data.get('session_id')
            print(f"Response: {data.get('message', data)[:200]}...")
            print(f"Action: {data.get('action')}")
            
            # If it asks for info, provide it
            if data.get('action') == 'ask_info':
                print(f"  -> AI is asking for: {data.get('missing_info')}")
        except Exception as e:
            print(f"Error: {e}")
        
        # Test 4: Set a reminder
        print("\n[Test 4] Set a reminder...")
        try:
            response = await client.post(f"{API_BASE}/chat", json={
                "message": "Remind me to call mom at 5pm today"
            })
            data = response.json()
            print(f"Response: {data.get('message', data)[:200]}...")
            print(f"Action: {data.get('action')}")
        except Exception as e:
            print(f"Error: {e}")
        
        # Test 5: General question (should use AI knowledge)
        print("\n[Test 5] General question...")
        try:
            response = await client.post(f"{API_BASE}/chat", json={
                "message": "What is the capital of Karnataka?"
            })
            data = response.json()
            print(f"Response: {data.get('message', data)[:200]}...")
            print(f"Action: {data.get('action')}")
        except Exception as e:
            print(f"Error: {e}")
        
        # Test 6: Quick meeting endpoint
        print("\n[Test 6] Quick meeting endpoint...")
        try:
            response = await client.post(f"{API_BASE}/quick/meeting", params={
                "title": "Sprint Planning",
                "participants": ["dev1@test.com", "dev2@test.com"],
                "time": "tomorrow 10am"
            })
            data = response.json()
            print(f"Response: {data.get('message', data)[:200]}...")
        except Exception as e:
            print(f"Error: {e}")
        
        print("\n" + "=" * 60)
        print("  TESTS COMPLETE")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_autonomous_ai())
