"""
Run SQL schemas on Supabase using Python supabase library
"""
from supabase import create_client
import os

# Supabase configuration
SUPABASE_URL = "https://hpqmcdygbjdmvxfmvucf.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhwcW1jZHlnYmpkbXZ4Zm12dWNmIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MDMwMjc2MywiZXhwIjoyMDg1ODc4NzYzfQ.TON1F1PcrTIhZMFdshHqYxbJIIxVc6du62Ri29sEpmc"
DB_PASSWORD = "Kiran@Google11"

def main():
    print("=" * 60)
    print("🗄️  SUPABASE DATABASE SETUP")
    print("=" * 60)
    
    # Create client
    print("\n🔌 Connecting to Supabase...")
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("   ✅ Connected!")
    
    # Read all schemas
    base_path = "backend/agent"
    schemas = [
        f"{base_path}/schema.sql",
        f"{base_path}/schema_orchestration.sql", 
        f"{base_path}/schema_identity.sql"
    ]
    
    all_sql = []
    for schema_file in schemas:
        try:
            print(f"\n📄 Reading {schema_file}...")
            with open(schema_file, 'r', encoding='utf-8') as f:
                sql = f.read()
            print(f"   Found {len(sql):,} characters")
            all_sql.append(sql)
        except FileNotFoundError:
            print(f"   ⚠️  Not found, skipping...")
    
    combined_sql = "\n\n".join(all_sql)
    
    # Save to file
    with open("COMBINED_SCHEMA.sql", 'w', encoding='utf-8') as f:
        f.write(combined_sql)
    print(f"\n✅ Combined SQL saved to COMBINED_SCHEMA.sql ({len(combined_sql):,} chars)")
    
    # Check existing tables
    print("\n📋 Checking existing tables...")
    try:
        # Check all tables
        base_tables = ['users', 'contacts', 'meetings', 'tasks', 'conversations', 'messages', 
                       'reminders', 'emails', 'fashion_profiles', 'travel_profiles', 'action_logs', 'preferences']
        orchestration_tables = ['agent_tasks', 'task_dependencies', 'workflow_templates', 'workflow_executions',
                                'autonomous_operations', 'user_access_tokens', 'delegated_permissions']
        identity_tables = ['ai_identities', 'ai_service_accounts', 'ai_decision_log', 
                           'ai_commitments', 'blocked_services', 'sensitive_data_requests']
        
        all_tables = base_tables + orchestration_tables + identity_tables
        
        existing = []
        missing = []
        
        for table in all_tables:
            try:
                supabase.table(table).select('*').limit(1).execute()
                existing.append(table)
            except:
                missing.append(table)
        
        print(f"   ✅ {len(existing)} tables exist")
        for t in existing:
            print(f"      • {t}")
        
        if missing:
            print(f"\n   ⚠️  {len(missing)} tables missing:")
            for t in missing:
                print(f"      • {t}")
        
    except Exception as e:
        print(f"   ⚠️  Tables need to be created")
        print(f"      Error: {str(e)[:100]}")
    
    # Instructions
    print("\n" + "=" * 60)
    print("📝 TO CREATE MISSING TABLES:")
    print("=" * 60)
    print("\n1. Go to your Supabase Dashboard:")
    print(f"   https://supabase.com/dashboard/project/hpqmcdygbjdmvxfmvucf/sql")
    print("\n2. Open COMBINED_SCHEMA.sql file")
    print("3. Copy the contents and paste into SQL Editor")
    print("4. Click 'Run' to execute")
    print("\n" + "=" * 60)
    
    return True

if __name__ == "__main__":
    main()
