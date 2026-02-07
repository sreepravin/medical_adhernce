#!/usr/bin/env python3
"""
Check adherence_summary table and connection
"""
import psycopg2
from psycopg2 import sql
import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', 5432))
DB_NAME = os.getenv('DB_NAME', 'postgres')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'root')

print("\n" + "="*60)
print("Testing Database Connection")
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
    print(f"✓ Connected to PostgreSQL at {DB_HOST}:{DB_PORT}/{DB_NAME}")
    
    cursor = conn.cursor()
    
    # Check if table exists
    cursor.execute("""
        SELECT EXISTS(
            SELECT 1 FROM information_schema.tables 
            WHERE table_name = 'adherence_summary'
        )
    """)
    
    table_exists = cursor.fetchone()[0]
    
    if table_exists:
        print("✓ Table 'adherence_summary' EXISTS\n")
        
        # Query the table
        cursor.execute("SELECT * FROM adherence_summary ORDER BY id DESC LIMIT 10")
        rows = cursor.fetchall()
        
        # Get column names
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'adherence_summary'
            ORDER BY ordinal_position
        """)
        columns = [col[0] for col in cursor.fetchall()]
        
        print(f"Columns: {', '.join(columns)}")
        print(f"Total rows in table: ", end="")
        cursor.execute("SELECT COUNT(*) FROM adherence_summary")
        print(cursor.fetchone()[0])
        
        print(f"\nRecent records:\n")
        for row in rows:
            print(dict(zip(columns, row)))
    else:
        print("✗ Table 'adherence_summary' DOES NOT EXIST")
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
    print(f"✗ Database Error: {str(e)}")
    print("\nMake sure PostgreSQL is running and .env values are correct:")
    print(f"  DB_HOST={DB_HOST}")
    print(f"  DB_PORT={DB_PORT}")
    print(f"  DB_NAME={DB_NAME}")
    print(f"  DB_USER={DB_USER}")

print("\n" + "="*60 + "\n")
