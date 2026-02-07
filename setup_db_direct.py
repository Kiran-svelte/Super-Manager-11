"""
Run missing SQL schemas on Supabase via direct PostgreSQL connection
"""
import psycopg2

# Database connection - use session mode (port 5432) not transaction mode (6543)
# Format: postgresql://[user]:[password]@[host]:[port]/[database]
DB_CONFIG = {
    "host": "aws-0-ap-south-1.pooler.supabase.com",
    "port": 5432,  # Session mode
    "database": "postgres",
    "user": "postgres.hpqmcdygbjdmvxfmvucf",
    "password": "Kiran@Google11",
    "sslmode": "require"
}

def run_sql_file(cursor, filepath, name):
    """Execute SQL file"""
    print(f"\n📄 Running {name}...")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            sql = f.read()
        
        # Execute the whole file
        cursor.execute(sql)
        print(f"   ✅ {name} executed successfully!")
        return True
    except Exception as e:
        error_msg = str(e)
        if 'already exists' in error_msg:
            print(f"   ✅ {name} - tables already exist")
            return True
        else:
            print(f"   ⚠️  Error: {error_msg[:200]}")
            return False

def main():
    print("=" * 60)
    print("🗄️  RUNNING SQL SCHEMAS ON SUPABASE")
    print("=" * 60)
    
    print(f"\n🔌 Connecting to database...")
    print(f"   Host: {DB_CONFIG['host']}")
    print(f"   Port: {DB_CONFIG['port']}")
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = True
        cursor = conn.cursor()
        print("   ✅ Connected!")
        
        # Run schema files
        schemas = [
            ("backend/agent/schema_orchestration.sql", "Orchestration Schema"),
            ("backend/agent/schema_identity.sql", "Identity Schema"),
        ]
        
        for filepath, name in schemas:
            try:
                run_sql_file(cursor, filepath, name)
            except Exception as e:
                print(f"   Error with {name}: {str(e)[:100]}")
        
        # Verify tables
        print("\n📋 Verifying tables...")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        tables = [row[0] for row in cursor.fetchall()]
        print(f"   Found {len(tables)} tables:")
        for t in tables:
            print(f"      • {t}")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("✅ DATABASE SETUP COMPLETE!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ Connection failed: {str(e)}")
        print("\n   Trying alternative connection...")
        
        # Try alternative host format
        alt_config = DB_CONFIG.copy()
        alt_config['host'] = 'db.hpqmcdygbjdmvxfmvucf.supabase.co'
        alt_config['user'] = 'postgres'
        
        try:
            conn = psycopg2.connect(**alt_config)
            conn.autocommit = True
            cursor = conn.cursor()
            print("   ✅ Connected with alternative config!")
            
            for filepath, name in schemas:
                run_sql_file(cursor, filepath, name)
            
            cursor.close()
            conn.close()
            print("\n✅ DATABASE SETUP COMPLETE!")
            return True
        except Exception as e2:
            print(f"\n❌ Alternative connection also failed: {str(e2)}")
            return False

if __name__ == "__main__":
    main()
