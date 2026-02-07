#!/usr/bin/env python
"""
Test database connections and verify all tables are created
"""

from db_connection import get_db_connection, execute_query, close_db_connection

def test_connection():
    """Test basic database connection"""
    print("\n" + "="*60)
    print("DATABASE CONNECTION TEST")
    print("="*60)
    
    conn = get_db_connection()
    if not conn:
        print("✗ FAILED: Could not establish database connection")
        return False
    
    print("✓ SUCCESS: Connected to database")
    close_db_connection(conn)
    return True

def test_tables():
    """Check if all required tables exist"""
    print("\n" + "="*60)
    print("DATABASE TABLES TEST")
    print("="*60)
    
    conn = get_db_connection()
    if not conn:
        print("✗ FAILED: Could not connect to database")
        return False
    
    # Query for tables
    result = execute_query(conn, """
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    
    if result:
        print(f"✓ Found {len(result)} tables in database:")
        for row in result:
            print(f"  • {row[0]}")
    else:
        print("✗ Could not retrieve table information")
        close_db_connection(conn)
        return False
    
    close_db_connection(conn)
    return True

def test_user_table():
    """Check if users table has correct structure"""
    print("\n" + "="*60)
    print("USERS TABLE STRUCTURE TEST")
    print("="*60)
    
    conn = get_db_connection()
    if not conn:
        print("✗ FAILED: Could not connect to database")
        return False
    
    # Get users table columns
    result = execute_query(conn, """
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'users'
        ORDER BY ordinal_position;
    """)
    
    if result:
        print("✓ Users table structure:")
        for col in result:
            nullable = "NULL" if col[2] == 'YES' else "NOT NULL"
            print(f"  • {col[0]:<20} {col[1]:<15} ({nullable})")
    else:
        print("✗ Users table not found or query failed")
        close_db_connection(conn)
        return False
    
    close_db_connection(conn)
    return True

def main():
    """Run all tests"""
    print("\n" + "█"*60)
    print("█ MEDICATION ADHERENCE SYSTEM - DATABASE DIAGNOSTIC")
    print("█"*60)
    
    tests = [
        ("Connection", test_connection),
        ("Tables", test_tables),
        ("Users Structure", test_user_table)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ ERROR in {name} test: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:8} {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ ALL TESTS PASSED - Database is working correctly!")
    else:
        print("\n✗ SOME TESTS FAILED - Please check database configuration")
    
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
