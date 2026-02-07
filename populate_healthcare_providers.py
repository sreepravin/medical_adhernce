#!/usr/bin/env python3
"""
Populate healthcare_providers table with sample data
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
print("Populating healthcare_providers table")
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
    
    # Get all users
    cursor.execute("SELECT id FROM users ORDER BY id")
    users = cursor.fetchall()
    
    if not users:
        print("✗ No users found in database")
    else:
        print(f"Found {len(users)} users\n")
        
        # Clear existing data
        cursor.execute("DELETE FROM healthcare_providers")
        deleted = cursor.rowcount
        print(f"Cleared {deleted} old records\n")
        
        # Sample healthcare providers
        providers_data = [
            {
                'provider_name': 'Dr. James Wilson',
                'provider_type': 'Primary Care Physician',
                'contact_email': 'jwilson@healthcenter.com',
                'contact_phone': '(555) 123-4567',
                'specialization': 'General Medicine'
            },
            {
                'provider_name': 'Dr. Sarah Chen',
                'provider_type': 'Cardiologist',
                'contact_email': 'schen@heartclinic.com',
                'contact_phone': '(555) 234-5678',
                'specialization': 'Cardiovascular Disease'
            },
            {
                'provider_name': 'Dr. Michael Rodriguez',
                'provider_type': 'Pharmacist',
                'contact_email': 'mrodriguez@pharmacy.com',
                'contact_phone': '(555) 345-6789',
                'specialization': 'Clinical Pharmacy'
            },
            {
                'provider_name': 'Dr. Emma Thompson',
                'provider_type': 'Endocrinologist',
                'contact_email': 'ethompson@diabetes.com',
                'contact_phone': '(555) 456-7890',
                'specialization': 'Diabetes Management'
            }
        ]
        
        print("Creating healthcare provider records:\n")
        count = 0
        
        for user in users:
            user_id = user[0]
            # Assign 1-2 providers per user
            num_providers = 1 if user_id % 2 == 0 else 2
            
            for i in range(min(num_providers, len(providers_data))):
                provider = providers_data[i]
                
                try:
                    cursor.execute("""
                        INSERT INTO healthcare_providers
                        (user_id, provider_name, provider_type, contact_email, 
                         contact_phone, specialization, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, NOW())
                    """, (
                        user_id,
                        provider['provider_name'],
                        provider['provider_type'],
                        provider['contact_email'],
                        provider['contact_phone'],
                        provider['specialization']
                    ))
                    
                    print(f"  ✓ User {user_id}: {provider['provider_name']} ({provider['provider_type']})")
                    count += 1
                except Exception as e:
                    print(f"  ✗ Error: {str(e)}")
        
        conn.commit()
        print(f"\n✓ Successfully inserted {count} healthcare provider records\n")
        
        # Show summary
        cursor.execute("""
            SELECT provider_type, COUNT(*) as count
            FROM healthcare_providers
            GROUP BY provider_type
            ORDER BY count DESC
        """)
        
        print("Summary by Provider Type:")
        for ptype, cnt in cursor.fetchall():
            print(f"  {ptype}: {cnt} providers")
        
        cursor.execute("""
            SELECT user_id, COUNT(*) as providers_count
            FROM healthcare_providers
            GROUP BY user_id
            ORDER BY user_id
        """)
        
        print("\nSummary by User:")
        for uid, cnt in cursor.fetchall():
            print(f"  User {uid}: {cnt} provider(s)")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"✗ Error: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60 + "\n")
