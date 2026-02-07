"""
Run the orchestration schema on Supabase
"""
import requests

SUPABASE_URL = "https://hpqmcdygbjdmvxfmvucf.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhwcW1jZHlnYmpkbXZ4Zm12dWNmIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MDMwMjc2MywiZXhwIjoyMDg1ODc4NzYzfQ.TON1F1PcrTIhZMFdshHqYxbJIIxVc6du62Ri29sEpmc"

from supabase import create_client

print("Creating orchestration tables...")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Check if tables exist by trying to query them
tables = ["orchestrated_tasks", "task_substeps", "scheduled_jobs", "meeting_participants", "notifications"]

for table in tables:
    try:
        result = supabase.table(table).select("count").limit(1).execute()
        print(f"  ✓ {table} exists")
    except Exception as e:
        if "does not exist" in str(e).lower() or "relation" in str(e).lower():
            print(f"  ✗ {table} needs to be created")
        else:
            print(f"  ? {table}: {e}")

print("\n" + "=" * 60)
print("NOTE: If tables don't exist, run this SQL in Supabase:")
print("https://supabase.com/dashboard/project/hpqmcdygbjdmvxfmvucf/sql/new")
print("=" * 60)
print("\nCopy the contents of: backend/agent/schema_orchestration.sql")
