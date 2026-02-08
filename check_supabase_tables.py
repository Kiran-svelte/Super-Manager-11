#!/usr/bin/env python
"""
Run migration on Supabase without direct PostgreSQL access
Uses REST API workaround
"""
import os
import requests
import json

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://hpqmcdygbjdmvxfmvucf.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

def table_exists(table_name):
    """Check if a table exists"""
    url = f"{SUPABASE_URL}/rest/v1/{table_name}?limit=0"
    response = requests.get(url, headers=headers)
    return response.status_code != 404

def create_table_via_insert(table_name, schema_url):
    """Create table by attempting insert (will fail but reveal if table exists)"""
    url = f"{SUPABASE_URL}/rest/v1/{table_name}"
    response = requests.get(url, headers=headers, params={"limit": "0"})
    return response.status_code == 200

# Tables to check
tables = [
    "users",
    "sessions",
    "messages", 
    "ai_identities",
    "ai_service_accounts",
    "ai_decision_log",
    "ai_commitments",
    "sensitive_data_requests",
    "blocked_services",
    "orchestrated_tasks",
    "task_substeps",
    "user_profiles",
    "user_contacts",
    "user_preferences"
]

print("=" * 60)
print("  SUPABASE TABLE CHECK")
print("=" * 60)
print(f"  URL: {SUPABASE_URL[:50]}...")
print()

existing = []
missing = []

for table in tables:
    if table_exists(table):
        print(f"  ✓ {table} exists")
        existing.append(table)
    else:
        print(f"  ✗ {table} MISSING")
        missing.append(table)

print()
print("=" * 60)
print(f"  Existing: {len(existing)}")
print(f"  Missing: {len(missing)}")
print("=" * 60)

if missing:
    print()
    print("  MISSING TABLES NEED TO BE CREATED IN SUPABASE SQL EDITOR:")
    print("  " + "-" * 56)
    for table in missing:
        print(f"    - {table}")
    print()
    print("  To create missing tables:")
    print("  1. Go to https://supabase.com/dashboard/project/hpqmcdygbjdmvxfmvucf/sql")
    print("  2. Copy and paste the contents of backend/agent/schema_identity.sql")
    print("  3. Run the SQL")
