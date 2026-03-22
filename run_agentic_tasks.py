import asyncio
import httpx
import json
import uuid

# Define a real user ID matched to the session
user_id = "real_e2e_user"
session_id = f"agent_session_{uuid.uuid4().hex[:8]}"
api_url = "http://localhost:8010/api/chat"

# The sequences to prove true multi-turn agentic tasking
agentic_sequences = [
    {
        "name": "1. Agentic Request (Email Request)",
        "prompt": "Please formulate and send an email to boss@company.com letting them know I am taking tomorrow off for health reasons."
    },
    {
        "name": "1-B. Agentic Confirmation (Approve Execution)",
        "prompt": "Yes, it looks good. Go ahead and send it."
    },
    {
        "name": "2. Agentic Request (Meeting Creation)",
        "prompt": "Set up a new video meeting link for tomorrow to discuss the new frontend designs."
    },
    {
        "name": "2-B. Agentic Confirmation (Approve Creation)",
        "prompt": "Yes, proceed with the meeting setup."
    },
    {
        "name": "3. Agentic Request (Schedule Reminder)",
        "prompt": "Create a reminder for me tomorrow at 9 AM to check the deployment logs."
    },
    {
        "name": "3-B. Agentic Confirmation (Approve Reminder)",
        "prompt": "Yes, set the reminder as stated."
    }
]

async def test_agentic_workflows():
    print("==================================================")
    print("🚀 RUNNING MULTI-TURN AGENTIC WORKFLOW TESTS")
    print(f"Session ID: {session_id}")
    print("==================================================\n")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        for step in agentic_sequences:
            print(f"--- {step['name']} ---")
            print(f"📥 User Input: {step['prompt']}")
            
            payload = {
                "message": step['prompt'],
                "session_id": session_id,
                "user_id": user_id
            }
            
            try:
                response = await client.post(api_url, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    
                    print("✅ AI Agent Logic Result:")
                    print("-" * 50)
                    
                    # Log the LLM's raw text response
                    if "message" in data:
                        print(f"💬 Chat Response: {data['message']}")
                    elif "response" in data:
                        print(f"💬 Chat Response: {data['response']}")
                        
                    # Check for tool call interrupts / pending actions natively
                    if data.get("requires_confirmation"):
                        print(f"\n⚡ AGENT STATE: Pausing execution. Waiting for user authorization!")
                        if "pending_action" in data and data["pending_action"]:
                            tool_name = data["pending_action"].get("tool")
                            print(f"🔧 PENDING TOOL: '{tool_name}' configured and ready to fire.")
                    
                    # Print full resulting JSON so we can see when the action executes successfully
                    print("\n[Raw Payload Context]:")
                    print(json.dumps({k: v for k, v in data.items() if k not in ["message", "response"]}, indent=2))
                    print("-" * 50 + "\n")
                    
                    # Add a small delay between tasks to mimic human interaction timing
                    await asyncio.sleep(2)
                else:
                    print(f"❌ Error: HTTP {response.status_code} - {response.text}\n")
            except Exception as e:
                print(f"❌ Exception: {e}\n")

if __name__ == "__main__":
    asyncio.run(test_agentic_workflows())