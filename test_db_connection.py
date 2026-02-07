#!/usr/bin/env python3
"""Test database connection and list all tables"""

from db_connection import get_db_connection, execute_query

try:
    conn = get_db_connection()
    print("✅ DATABASE CONNECTION SUCCESSFUL!")
    
    # Get tables
    result = execute_query(conn, """
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    
    tables = [row[0] for row in result]
    print(f"\n✅ Found {len(tables)} tables created:")
    print("-" * 40)
    for i, table in enumerate(tables, 1):
        print(f"  {i:2}. {table}")
    
    # Get row counts
    print("\n✅ Table row counts:")
    print("-" * 40)
    for table in tables:
        try:
            count = execute_query(conn, f"SELECT COUNT(*) FROM {table};")
            rows = count[0][0] if count else 0
            print(f"  {table:30} → {rows:5} rows")
        except:
            print(f"  {table:30} → error reading")
    
    conn.close()
    print("\n✅ Database is fully connected and ready!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
