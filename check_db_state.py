#!/usr/bin/env python
"""Check current database state"""

from db_connection import get_db_connection, execute_query, close_db_connection

conn = get_db_connection()
if conn:
    # Check all prescriptions in database
    all_rx = execute_query(conn, 'SELECT id, user_id, medicine_name, created_at FROM prescriptions ORDER BY created_at DESC LIMIT 20')
    if all_rx:
        print(f'✓ Found {len(all_rx)} prescriptions in database:')
        for rx in all_rx:
            print(f'  ID: {rx[0]} | User: {rx[1]} | Medicine: {rx[2]} | Created: {rx[3]}')
    else:
        print('✗ No prescriptions in database')
    
    # Check all users
    print()
    users = execute_query(conn, 'SELECT id, username, created_at FROM users ORDER BY id')
    if users:
        print(f'✓ Found {len(users)} users in database:')
        for u in users:
            print(f'  ID: {u[0]} | Username: {u[1]} | Created: {u[2]}')
    
    close_db_connection(conn)
