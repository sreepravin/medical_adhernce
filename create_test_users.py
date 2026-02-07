#!/usr/bin/env python3
"""Create test users for login testing"""

from db_connection import get_db_connection

try:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check existing users
    cursor.execute('SELECT COUNT(*) FROM users')
    count = cursor.fetchone()[0]
    
    print(f"Current users in database: {count}")
    
    # Insert test users
    cursor.execute('''
        INSERT INTO users (username, email, password_hash, full_name)
        VALUES (%s, %s, %s, %s), (%s, %s, %s, %s)
        ON CONFLICT (username) DO NOTHING
    ''', ('admin', 'admin@test.com', 'admin123', 'Admin User',
          'user1', 'user1@test.com', 'user123', 'Test User'))
    
    conn.commit()
    
    # Show all users
    cursor.execute('SELECT id, username, email, full_name FROM users ORDER BY id')
    users = cursor.fetchall()
    
    print(f"\n✅ Test users created/verified!")
    print(f"Total users now: {len(users)}\n")
    print("Available test logins:")
    print("-" * 50)
    for user in users:
        print(f"  ID: {user[0]}, Username: {user[1]}, Email: {user[2]}")
    
    print("\nTest Credentials:")
    print("-" * 50)
    print("  Username: admin, Password: admin123")
    print("  Username: user1, Password: user123")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
