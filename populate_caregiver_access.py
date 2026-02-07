#!/usr/bin/env python3
"""
Populate caregiver_access table with sample data
"""
import psycopg2
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', 5432))
DB_NAME = os.getenv('DB_NAME', 'postgres')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'root')

print("\n" + "="*60)
print("Populating caregiver_access table")
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
    
    # First get all users
    cursor.execute("SELECT id, username FROM users ORDER BY id")
    users = cursor.fetchall()
    
    if len(users) < 2:
        print("✗ Need at least 2 users to create caregiver relationships")
        print(f"   Found only {len(users)} user(s)")
    else:
        print(f"Found {len(users)} users in database:\n")
        for uid, uname in users:
            print(f"  User {uid}: {uname}")
        
        # Clear existing data
        cursor.execute("DELETE FROM caregiver_access")
        deleted = cursor.rowcount
        print(f"\nCleared {deleted} old records\n")
        
        # Create caregiver relationships
        print("Creating caregiver relationships:\n")
        count = 0
        
        # Example: User 15 (caregiver) has access to User 14 (patient)
        caregiver_relationships = []
        
        # Make first user a caregiver for second user
        if len(users) >= 2:
            caregiver_relationships.append({
                'patient_user_id': users[1][0],
                'caregiver_user_id': users[0][0],
                'access_level': 'full'
            })
        
        # Make second user a caregiver for first user (if 3+ users exist)
        if len(users) >= 3:
            caregiver_relationships.append({
                'patient_user_id': users[0][0],
                'caregiver_user_id': users[1][0],
                'access_level': 'view_only'
            })
        
        # If we have user 14 and 15, create both directions
        # This covers the common scenario
        for rel in caregiver_relationships:
            try:
                cursor.execute("""
                    INSERT INTO caregiver_access 
                    (patient_user_id, caregiver_user_id, access_level, granted_at)
                    VALUES (%s, %s, %s, NOW())
                """, (rel['patient_user_id'], rel['caregiver_user_id'], rel['access_level']))
                
                patient = next((u[1] for u in users if u[0] == rel['patient_user_id']), 'Unknown')
                caregiver = next((u[1] for u in users if u[0] == rel['caregiver_user_id']), 'Unknown')
                
                print(f"  ✓ {caregiver} (caregiver) → {patient} (patient) [{rel['access_level']}]")
                count += 1
            except Exception as e:
                print(f"  ✗ Error: {str(e)}")
        
        conn.commit()
        print(f"\n✓ Successfully inserted {count} caregiver access records\n")
        
        # Show summary
        cursor.execute("""
            SELECT ca.id, u1.username as caregiver, u2.username as patient, ca.access_level, ca.granted_at
            FROM caregiver_access ca
            JOIN users u1 ON ca.caregiver_user_id = u1.id
            JOIN users u2 ON ca.patient_user_id = u2.id
            ORDER BY ca.granted_at DESC
        """)
        
        print("Caregiver Access Summary:")
        for row in cursor.fetchall():
            print(f"  ID {row[0]}: {row[1]} has {row[3]} access to {row[2]} (granted: {row[4]})")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"✗ Error: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60 + "\n")
