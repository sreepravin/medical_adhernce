#!/usr/bin/env python3
"""Create database schema directly from SQL file"""

from db_connection import get_db_connection
import psycopg2.extensions

# Read schema file
with open('schema.sql', 'r') as f:
    schema_content = f.read()

try:
    conn = get_db_connection()
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    
    cursor = conn.cursor()
    
    # Replace ``` markers if present
    schema_content = schema_content.replace('```oraclesql\n', '').replace('```\n', '').replace('```', '')
    
    print("✅ Connected to database")
    print("📝 Executing schema.sql...")
    
    # Execute entire schema
    cursor.execute(schema_content)
    
    print("✅ Schema executed successfully!")
    
    # Check what tables exist now
    cursor.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    
    tables = cursor.fetchall()
    print(f"\n✅ Created {len(tables)} tables:")
    print("-" * 50)
    
    for (table,) in sorted(tables):
        cursor.execute(f"SELECT COUNT(*) FROM {table};")
        count = cursor.fetchone()[0]
        print(f"  ✓ {table:35} ({count:7} rows)")
    
    cursor.close()
    conn.close()
    
    print("\n✅ Database setup complete and verified!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
