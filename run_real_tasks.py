import asyncio
import httpx
import json
import uuid

session_id = f"test_session_{uuid.uuid4().hex[:8]}"

tasks = [
    {
        "name": "1. Logic/Math",
        "prompt": "If I have 15 boxes of 90 apples each, how many apples do I have in total?",
    },
    {
        "name": "2. Memory Saving",
        "prompt": "Remember that my favorite framework is absolute Svelte.",
    },
    {
        "name": "3. Memory Recall",
        "prompt": "What did I just tell you my favorite framework was?",
    },
    {
        "name": "4. Task Creation",
        "prompt": "Add a task 'Read the documentation for SvelteKit' to my todo list.",
    },
    {
        "name": "5. Code Extraction",
        "prompt": "Extract the names and ages directly into a bulleted list: John is 25, Mary is 32, and Bob who is 40 went to the store. Do not write python code, just return the list.",
    },
    {
        "name": "6. Content Summarization",
        "prompt": "Summarize this in exactly 4 words: The Industrial Revolution was the transition to new manufacturing processes in Great Britain, continental Europe, and the United States, that occurred during the period from around 1760 to about 1820-1840.",
    },
    {
        "name": "7. Translation",
        "prompt": "Translate exactly: 'The system is operational.' to French.",
    },
    {
        "name": "8. Tool: Python Data Format",
        "prompt": "Execute python code to sort this array strictly in descending order and return clearly formatted text: [9, 2, 7, 10, 4]",
    },
    {
        "name": "9. Directory Listing Tool",
        "prompt": "Use python to list the top level files in this directory where you run and tell me 2 files you see.",
    },
    {
        "name": "10. Reasoning Constraint",
        "prompt": "Why is the sky blue? Explain in exactly 8 words.",
    }
]

async def test_agent():
    print("==================================================")
    print("🚀 RUNNING 10 REAL TASKS WITH TRUE CONTEXT/MEMORY")
    print(f"Session ID: {session_id}")
    print("==================================================\n")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        for t in tasks:
            print(f"--- {t['name']} ---")
            print(f"📥 Prompt: {t['prompt']}")
            
            payload = {
                "message": t["prompt"],
                "session_id": session_id,
                "user_id": "real_e2e_user"
            }
            
            try:
                response = await client.post("http://localhost:8010/api/chat", json=payload)
                if response.status_code == 200:
                    data = response.json()
                    print("✅ Response from Agent:")
                    print("-" * 40)
                    if "message" in data:
                        print(data["message"])
                    elif "response" in data:
                        print(data["response"])
                    else:
                        print(json.dumps(data, indent=2))
                    print("-" * 40 + "\n")
                else:
                    print(f"❌ Error: HTTP {response.status_code} - {response.text}\n")
            except Exception as e:
                print(f"❌ Exception: {e}\n")

if __name__ == "__main__":
    asyncio.run(test_agent())
