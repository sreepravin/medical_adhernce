#!/usr/bin/env python3
"""
Check contraindication_checks table and connection
"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', 5432))
DB_NAME = os.getenv('DB_NAME', 'postgres')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'root')

print("\n" + "="*60)
print("Testing contraindication_checks Table")
print("="*60 + "\n")

try:
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        connect_timeout=10
    )
    print(f"✓ Connected to PostgreSQL\n")
    
    cursor = conn.cursor()
    
    # Check if table exists
    cursor.execute("""
        SELECT EXISTS(
            SELECT 1 FROM information_schema.tables 
            WHERE table_name = 'contraindication_checks'
        )
    """)
    
    table_exists = cursor.fetchone()[0]
    
    if table_exists:
        print("✓ Table 'contraindication_checks' EXISTS\n")
        
        # Get columns
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'contraindication_checks'
            ORDER BY ordinal_position
        """)
        columns = [col[0] for col in cursor.fetchall()]
        print(f"Columns: {', '.join(columns)}\n")
        
        # Count rows
        cursor.execute("SELECT COUNT(*) FROM contraindication_checks")
        count = cursor.fetchone()[0]
        print(f"Total rows: {count}")
        
        if count > 0:
            print(f"\nRecent records:\n")
            cursor.execute("SELECT * FROM contraindication_checks LIMIT 5")
            rows = cursor.fetchall()
            for row in rows:
                print(f"  {dict(zip(columns, row))}")
        else:
            print("✗ Table is EMPTY (0 rows)\n")
            print("Need to populate with contraindication check data")
    else:
        print("✗ Table 'contraindication_checks' DOES NOT EXIST")
        print("\nAvailable tables in database:\n")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        for table in tables:
            print(f"  - {table[0]}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"✗ Error: {str(e)}")

print("\n" + "="*60 + "\n")
