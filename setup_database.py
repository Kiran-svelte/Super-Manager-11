"""
Run all SQL schemas on Supabase via REST API
"""
import requests
import os

# Supabase connection details
SUPABASE_URL = "https://hpqmcdygbjdmvxfmvucf.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhwcW1jZHlnYmpkbXZ4Zm12dWNmIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MDMwMjc2MywiZXhwIjoyMDg1ODc4NzYzfQ.TON1F1PcrTIhZMFdshHqYxbJIIxVc6du62Ri29sEpmc"

def run_schema(schema_file: str):
    """Run a SQL schema file"""
    print(f"\n📄 Reading {schema_file}...")
    
    with open(schema_file, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    print(f"   Found {len(sql)} characters of SQL")
    return sql

def execute_sql(sql: str, description: str = ""):
    """Execute SQL via Supabase REST API"""
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    
    # Use the SQL endpoint
    url = f"{SUPABASE_URL}/rest/v1/rpc/exec_sql"
    
    response = requests.post(url, headers=headers, json={"query": sql})
    return response

def main():
    print("=" * 60)
    print("🗄️  SUPABASE DATABASE SETUP")
    print("=" * 60)
    
    # Read all schema files
    base_path = "backend/agent"
    schemas = [
        f"{base_path}/schema.sql",
        f"{base_path}/schema_orchestration.sql", 
        f"{base_path}/schema_identity.sql"
    ]
    
    all_sql = []
    for schema in schemas:
        try:
            sql = run_schema(schema)
            all_sql.append(sql)
        except FileNotFoundError:
            print(f"   ⚠️  {schema} not found, skipping...")
    
    combined_sql = "\n\n".join(all_sql)
    
    # Save combined SQL for manual use
    output_file = "COMBINED_SCHEMA.sql"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(combined_sql)
    print(f"\n✅ Combined SQL saved to {output_file}")
    print(f"   Total: {len(combined_sql):,} characters")
    
    # Try to execute via REST API
    print(f"\n🔌 Testing Supabase connection...")
    
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
    }
    
    # Test connection by listing tables
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/",
        headers=headers
    )
    
    if response.status_code == 200:
        print("   ✅ Supabase connection works!")
        
        # Check what tables exist
        print("\n📋 Checking existing tables...")
        
        # Try to query users table
        test_response = requests.get(
            f"{SUPABASE_URL}/rest/v1/users?select=id&limit=1",
            headers=headers
        )
        
        if test_response.status_code == 200:
            print("   ✅ 'users' table exists!")
        elif test_response.status_code == 404:
            print("   ⚠️  'users' table doesn't exist yet")
            print("\n📝 Please run the SQL in Supabase Dashboard:")
            print(f"   1. Go to: {SUPABASE_URL.replace('https://', 'https://supabase.com/dashboard/project/').replace('.supabase.co', '')}/sql")
            print(f"   2. Copy contents of {output_file}")
            print("   3. Paste and click 'Run'")
        else:
            print(f"   Response: {test_response.status_code}")
            
    else:
        print(f"   ⚠️  Connection issue: {response.status_code}")
    
    print("\n" + "=" * 60)
    print("📁 SQL files combined successfully!")
    print(f"   File: {output_file}")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    main()
