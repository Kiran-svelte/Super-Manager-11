"""Test API Keys"""
import httpx
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def test_apis():
    print("Testing API Keys...")
    print("="*50)
    
    # Test Groq
    groq_key = os.getenv("GROQ_API_KEY")
    groq_model = os.getenv("GROQ_MODEL", "llama-3.2-90b-text-preview")
    print(f"GROQ_API_KEY: {groq_key[:20] if groq_key else 'NOT SET'}...")
    print(f"GROQ_MODEL: {groq_model}")
    
    if groq_key:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                r = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {groq_key}"},
                    json={
                        "model": groq_model,
                        "messages": [{"role": "user", "content": "Say hello in 3 words"}],
                        "max_tokens": 20
                    }
                )
                if r.status_code == 200:
                    data = r.json()
                    content = data["choices"][0]["message"]["content"]
                    print(f"Groq: ✅ WORKING! Response: {content}")
                else:
                    print(f"Groq: ❌ Error {r.status_code}")
                    print(f"  Details: {r.text[:200]}")
        except Exception as e:
            print(f"Groq: ❌ {e}")
    
    print()
    
    # Test OpenAI
    openai_key = os.getenv("OPENAI_API_KEY")
    print(f"OPENAI_API_KEY: {openai_key[:20] if openai_key else 'NOT SET'}...")
    
    if openai_key:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                r = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {openai_key}"},
                    json={
                        "model": "gpt-3.5-turbo",
                        "messages": [{"role": "user", "content": "Say hello in 3 words"}],
                        "max_tokens": 20
                    }
                )
                if r.status_code == 200:
                    data = r.json()
                    content = data["choices"][0]["message"]["content"]
                    print(f"OpenAI: ✅ WORKING! Response: {content}")
                else:
                    print(f"OpenAI: ❌ Error {r.status_code}")
                    print(f"  Details: {r.text[:200]}")
        except Exception as e:
            print(f"OpenAI: ❌ {e}")
    
    print()
    print("="*50)

if __name__ == "__main__":
    asyncio.run(test_apis())
