import asyncio
import httpx
import json

async def test_zoom():
    session_id = "test_zoom_integration"
    user_id = "test_user_no_zoom"
    url = "http://localhost:8010/api/chat"
    
    payload = {
        "message": "Create a Zoom meeting for tomorrow 3pm with kiranlighter11@gmail.com",
        "session_id": session_id,
        "user_id": user_id
    }
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=payload, timeout=60.0)
        data = resp.json()
        print(json.dumps(data, indent=2))

if __name__ == "__main__":
    asyncio.run(test_zoom())