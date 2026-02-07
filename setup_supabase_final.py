"""
Setup Supabase Database with Service Role Key
"""
import os
import sys

# Supabase credentials
SUPABASE_URL = "https://hpqmcdygbjdmvxfmvucf.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhwcW1jZHlnYmpkbXZ4Zm12dWNmIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MDMwMjc2MywiZXhwIjoyMDg1ODc4NzYzfQ.TON1F1PcrTIhZMFdshHqYxbJIIxVc6du62Ri29sEpmc"

# Read SQL schema
schema_path = os.path.join(os.path.dirname(__file__), "backend", "agent", "schema.sql")
with open(schema_path, 'r') as f:
    sql_schema = f.read()

print("=" * 60)
print("SUPABASE DATABASE SETUP - SERVICE ROLE")
print("=" * 60)

import requests

headers = {
    "apikey": SUPABASE_SERVICE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

# Test connection
print("\n[1] Testing connection...")
resp = requests.get(f"{SUPABASE_URL}/rest/v1/", headers=headers)
print(f"    API Status: {resp.status_code}")

# The Supabase REST API doesn't support raw DDL
# We need to use the SQL endpoint or direct PostgreSQL connection
# Let's try the postgrest RPC approach first

# For DDL, we need to use the Supabase Management API or direct connection
# The service role key allows us to use the database directly

# Get the database connection string
# Format: postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres

# Extract project ref from URL
project_ref = "hpqmcdygbjdmvxfmvucf"

# The password is in the service role JWT - but we need the actual DB password
# Let's try using psycopg2 with the pooler connection

print("\n[2] Trying direct PostgreSQL connection...")

# Supabase provides a connection pooler at:
# postgresql://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres

# Since we have the service role key, let's try the REST approach with SQL
# Supabase has a hidden SQL execution endpoint

# Actually, let's use the supabase-py library with service role
from supabase import create_client, Client

print("\n[3] Connecting with service role...")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
print("    ✓ Connected with service role!")

# The supabase-py client with service role has admin access
# But it still doesn't support raw DDL directly
# We need to use RPC or the SQL API

# Let's check if tables already exist
print("\n[4] Checking existing tables...")
try:
    # Try to query users table
    result = supabase.table("users").select("*").limit(1).execute()
    print("    ✓ 'users' table exists!")
    tables_exist = True
except Exception as e:
    if "does not exist" in str(e) or "relation" in str(e).lower():
        print("    ✗ Tables don't exist yet")
        tables_exist = False
    else:
        print(f"    ? Error: {e}")
        tables_exist = False

if tables_exist:
    print("\n[5] Tables already exist! Checking all tables...")
    tables = ["users", "contacts", "preferences", "conversations", "messages", 
              "meetings", "reminders", "tasks", "emails", "fashion_profiles", 
              "travel_profiles", "action_logs"]
    
    for table in tables:
        try:
            result = supabase.table(table).select("count").limit(1).execute()
            print(f"    ✓ {table}")
        except Exception as e:
            print(f"    ✗ {table}: {e}")
    
    print("\n" + "=" * 60)
    print("DATABASE IS READY!")
    print("=" * 60)
else:
    print("\n[5] Need to create tables...")
    print("    The SQL needs to be run in Supabase SQL Editor or via direct connection.")
    
    # Try using the Supabase Management API
    print("\n[6] Attempting via Supabase REST SQL endpoint...")
    
    # Split schema into individual statements
    statements = []
    current = []
    in_function = False
    
    for line in sql_schema.split('\n'):
        stripped = line.strip()
        
        # Skip comments and empty lines
        if stripped.startswith('--') or not stripped:
            continue
        
        # Track if we're inside a function definition
        if 'CREATE OR REPLACE FUNCTION' in stripped.upper() or 'CREATE FUNCTION' in stripped.upper():
            in_function = True
        
        current.append(line)
        
        # End of statement
        if stripped.endswith(';') and not in_function:
            statements.append('\n'.join(current))
            current = []
        elif in_function and stripped == '$$ LANGUAGE plpgsql;':
            statements.append('\n'.join(current))
            current = []
            in_function = False
    
    print(f"    Found {len(statements)} SQL statements")
    
    # The Supabase PostgREST doesn't have a SQL endpoint
    # We need to use the database URL directly
    
    print("\n" + "=" * 60)
    print("MANUAL STEP REQUIRED")
    print("=" * 60)
    print("\nPlease run the SQL schema in Supabase SQL Editor:")
    print(f"https://supabase.com/dashboard/project/{project_ref}/sql/new")
    print("\nOr provide the database password for direct connection.")
    print("Go to: https://supabase.com/dashboard/project/{project_ref}/settings/database")
    print("=" * 60)

# Test inserting a user
print("\n[7] Testing write access...")
try:
    test_user = {
        "email": "test@example.com",
        "name": "Test User"
    }
    # This will fail if table doesn't exist
    result = supabase.table("users").upsert(test_user, on_conflict="email").execute()
    print("    ✓ Write access confirmed!")
    print(f"    Created/updated user: {result.data}")
except Exception as e:
    print(f"    ✗ Write test failed: {e}")
    print("    Tables may not exist yet. Please run the SQL schema first.")
