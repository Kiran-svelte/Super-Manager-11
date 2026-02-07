"""
Run orchestration schema on Supabase
"""
import httpx
import os

SUPABASE_URL = "https://hpqmcdygbjdmvxfmvucf.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhwcW1jZHlnYmpkbXZ4Zm12dWNmIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MDMwMjc2MywiZXhwIjoyMDg1ODc4NzYzfQ.TON1F1PcrTIhZMFdshHqYxbJIIxVc6du62Ri29sEpmc"

def run_sql(sql: str):
    """Execute SQL using Supabase RPC/REST"""
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json"
    }
    
    # Use the SQL endpoint
    url = f"{SUPABASE_URL}/rest/v1/rpc/exec_sql"
    
    response = httpx.post(url, json={"query": sql}, headers=headers)
    return response

def run_raw_sql_via_postgres():
    """Run SQL via Supabase Postgres REST endpoint"""
    import psycopg2
    
    # Supabase connection string
    conn_string = f"postgresql://postgres.hpqmcdygbjdmvxfmvucf:@aws-0-ap-south-1.pooler.supabase.com:6543/postgres"
    
    print("This requires direct database access via the Supabase Dashboard.")
    print("\nPlease follow these steps:")
    print("1. Go to https://supabase.com/dashboard")
    print("2. Select your project (hpqmcdygbjdmvxfmvucf)")
    print("3. Go to SQL Editor")
    print("4. Copy and paste the contents of backend/agent/schema_orchestration.sql")
    print("5. Click 'Run'")
    print("\nAlternatively, you can provide your database password for direct connection.")

def check_tables():
    """Check if tables exist"""
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json"
    }
    
    tables = ["orchestrated_tasks", "task_substeps", "scheduled_jobs", "meeting_participants", "notifications"]
    
    print("Checking if orchestration tables exist...")
    
    for table in tables:
        url = f"{SUPABASE_URL}/rest/v1/{table}?limit=1"
        response = httpx.get(url, headers=headers)
        if response.status_code == 200:
            print(f"  ✓ {table} exists")
        else:
            print(f"  ✗ {table} NOT found (need to run schema)")
    
    return response.status_code == 200

if __name__ == "__main__":
    # First check if tables exist
    if not check_tables():
        print("\n" + "="*60)
        run_raw_sql_via_postgres()
        print("="*60)
