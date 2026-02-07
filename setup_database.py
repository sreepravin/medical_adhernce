#!/usr/bin/env python3
"""Create all database tables if they don't exist"""

from db_connection import get_db_connection, execute_update
import traceback

# Read schema file
with open('schema.sql', 'r') as f:
    schema_content = f.read()

try:
    conn = get_db_connection()
    print("✅ Connected to database")
    
    # Split by semicolon and execute each statement
    statements = schema_content.split(';')
    table_count = 0
    
    for statement in statements:
        statement = statement.strip()
        if statement and not statement.startswith('--'):
            try:
                execute_update(conn, statement)
                if 'CREATE TABLE' in statement.upper():
                    table_count += 1
                    # Extract table name
                    table_name = statement.split('CREATE TABLE IF NOT EXISTS')[1].strip().split('(')[0].strip()
                    print(f"✅ Created table: {table_name}")
            except Exception as e:
                if 'already exists' in str(e):
                    print(f"⚠️  Table already exists (skipping): {statement[:50]}...")
                else:
                    print(f"❌ Error executing: {statement[:50]}...")
                    print(f"   Error: {e}")
    
    print(f"\n✅ Database schema setup complete!")
    print(f"✅ Created/verified {table_count} tables")
    
    # List all tables
    from db_connection import execute_query
    result = execute_query(conn, """
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    
    tables = [row[0] for row in result]
    print(f"\n📊 All tables in database ({len(tables)} total):")
    print("-" * 50)
    for table in tables:
        count = execute_query(conn, f"SELECT COUNT(*) FROM {table};")
        rows = count[0][0] if count else 0
        print(f"  • {table:30} ({rows:6} rows)")
    
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    traceback.print_exc()
