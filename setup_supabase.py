"""
Setup Supabase Database Schema
Runs the SQL schema on Supabase
"""
import os
import sys

# Supabase credentials
SUPABASE_URL = "https://hpqmcdygbjdmvxfmvucf.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhwcW1jZHlnYmpkbXZ4Zm12dWNmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzAzMDI3NjMsImV4cCI6MjA4NTg3ODc2M30.ToU0CnHo5WHo_qzpNadljZrgnfRW06rhsvGIPBpdXBw"

# Read SQL schema
schema_path = os.path.join(os.path.dirname(__file__), "backend", "agent", "schema.sql")
with open(schema_path, 'r') as f:
    sql_schema = f.read()

print("=" * 60)
print("SUPABASE DATABASE SETUP")
print("=" * 60)
print(f"Project URL: {SUPABASE_URL}")
print(f"Schema file: {schema_path}")
print(f"Schema size: {len(sql_schema)} characters")
print("=" * 60)

# Try using supabase-py
try:
    from supabase import create_client, Client
    
    print("\n[1] Connecting to Supabase...")
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    print("    ✓ Connected!")
    
    # The supabase-py client doesn't directly support raw SQL execution
    # We need to use the SQL Editor API or direct PostgreSQL connection
    print("\n[!] Note: supabase-py doesn't support raw DDL.")
    print("    Trying alternative method...")
    
except Exception as e:
    print(f"\n[!] Supabase client error: {e}")

# Try using direct REST API with SQL endpoint
import requests

print("\n[2] Trying Supabase SQL REST API...")

# Supabase has an RPC endpoint for executing SQL
# But it requires the service_role key for DDL operations

headers = {
    "apikey": SUPABASE_ANON_KEY,
    "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
    "Content-Type": "application/json"
}

# Test connection first
try:
    resp = requests.get(f"{SUPABASE_URL}/rest/v1/", headers=headers)
    print(f"    API Status: {resp.status_code}")
    if resp.status_code == 200:
        print("    ✓ API is accessible!")
except Exception as e:
    print(f"    ✗ API error: {e}")

# The Supabase Management API is at api.supabase.com
# It requires a personal access token, not the anon key

print("\n" + "=" * 60)
print("IMPORTANT: To run DDL (CREATE TABLE), I need either:")
print("=" * 60)
print("\n1. Database Password (direct PostgreSQL connection)")
print("   Go to: https://supabase.com/dashboard/project/hpqmcdygbjdmvxfmvucf/settings/database")
print("   Copy the 'Connection string' or 'Password'")
print("\n2. Service Role Key (has admin permissions)")
print("   Go to: https://supabase.com/dashboard/project/hpqmcdygbjdmvxfmvucf/settings/api")
print("   Copy the 'service_role' key (NOT the anon key)")
print("\n" + "=" * 60)

# Try anyway with anon key via the RPC endpoint
print("\n[3] Attempting SQL execution via RPC (may fail)...")

# Split SQL into smaller chunks (individual statements)
statements = []
current = ""
for line in sql_schema.split('\n'):
    line = line.strip()
    if line.startswith('--') or not line:
        continue
    current += line + " "
    if line.endswith(';'):
        statements.append(current.strip())
        current = ""

print(f"    Found {len(statements)} SQL statements")

# Try a simple test query first
test_query = "SELECT current_database(), current_user, version();"
try:
    # Using PostgREST RPC
    # This won't work for DDL, but let's try
    resp = requests.post(
        f"{SUPABASE_URL}/rest/v1/rpc/execute_sql",
        headers=headers,
        json={"query": test_query}
    )
    if resp.status_code == 200:
        print(f"    ✓ SQL execution works!")
    else:
        print(f"    Note: RPC endpoint not available ({resp.status_code})")
        print(f"    This is expected - Supabase needs service_role key for DDL")
except Exception as e:
    print(f"    Note: {e}")

print("\n" + "=" * 60)
print("NEXT STEP: Please provide ONE of these:")
print("=" * 60)
print("\nOption A - Service Role Key:")
print("  1. Go to: https://supabase.com/dashboard/project/hpqmcdygbjdmvxfmvucf/settings/api")
print("  2. Scroll to 'Project API keys'")
print("  3. Copy the 'service_role' key")
print("\nOption B - Database Password:")
print("  1. Go to: https://supabase.com/dashboard/project/hpqmcdygbjdmvxfmvucf/settings/database")
print("  2. Copy the password under 'Connection string'")
print("\n" + "=" * 60)
