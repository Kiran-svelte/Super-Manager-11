"""Test API keys to find working ones"""
import asyncio
import os
from dotenv import load_dotenv
load_dotenv('backend/.env')

async def test_apis():
    results = {"openai": False, "groq": False}
    
    # Test OpenAI
    try:
        import openai
        client = openai.AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        response = await client.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=[{'role': 'user', 'content': 'Say hello in 5 words'}],
            max_tokens=20
        )
        print(f'OpenAI: ✅ WORKING - {response.choices[0].message.content}')
        results["openai"] = True
    except Exception as e:
        print(f'OpenAI: ❌ {str(e)[:150]}')
    
    # Test Groq
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                'https://api.groq.com/openai/v1/chat/completions',
                headers={'Authorization': f"Bearer {os.getenv('GROQ_API_KEY')}"},
                json={'model': 'llama3-8b-8192', 'messages': [{'role': 'user', 'content': 'Hi'}], 'max_tokens': 10},
                timeout=30
            )
            if resp.status_code == 200:
                print(f'Groq: ✅ WORKING')
                results["groq"] = True
            else:
                print(f'Groq: ❌ {resp.status_code} - {resp.text[:150]}')
    except Exception as e:
        print(f'Groq: ❌ {str(e)[:150]}')
    
    return results

if __name__ == "__main__":
    results = asyncio.run(test_apis())
    print(f"\nWorking APIs: {[k for k,v in results.items() if v]}")
