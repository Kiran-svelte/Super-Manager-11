#!/usr/bin/env python
"""Try to connect to Supabase and run migrations"""
import psycopg2
import os

# Connection params
host = 'aws-0-ap-south-1.pooler.supabase.com'
port = 6543
database = 'postgres'
user = 'postgres.hpqmcdygbjdmvxfmvucf'
password = 'Kiran@Google11'

print("Attempting PostgreSQL connection to Supabase...")
print(f"Host: {host}")
print(f"Port: {port}")
print(f"User: {user}")
print()

try:
    conn = psycopg2.connect(
        host=host,
        port=port,
        database=database,
        user=user,
        password=password,
        sslmode='require',
        connect_timeout=15
    )
    print("Connected successfully!")
    
    cursor = conn.cursor()
    
    # List existing tables
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)
    tables = cursor.fetchall()
    
    print(f"\nFound {len(tables)} existing tables:")
    for t in tables:
        print(f"  - {t[0]}")
    
    conn.close()
    print("\nConnection test successful!")
    
except Exception as e:
    print(f"Connection failed: {e}")
    print("\nNote: If connection fails, run the SQL in Supabase SQL Editor manually.")
