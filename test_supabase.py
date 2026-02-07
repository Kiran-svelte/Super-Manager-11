"""Test Supabase connection"""
import requests

# Key from Render (correct one)
SUPABASE_URL = "https://hpqmcdygbjdmvxfmvucf.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhwcW1jZHlnYmpkbXZ4Zm12dWNmIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MDMwMjc2MywiZXhwIjoyMDg1ODc4NzYzfQ.TON1F1PcrTIhZMFdshHqYxbJIIxVc6du62Ri29sEpmc"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}"
}

# Test connection
r = requests.get(f"{SUPABASE_URL}/rest/v1/", headers=headers)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    print("✅ Supabase connection works!")
    print(f"Tables: {r.text[:500]}")
else:
    print(f"Response: {r.text}")
