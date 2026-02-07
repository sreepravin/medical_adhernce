#!/usr/bin/env python3
"""
Populate contraindication_checks table with sample data
"""
import psycopg2
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import random

load_dotenv()

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', 5432))
DB_NAME = os.getenv('DB_NAME', 'postgres')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'root')

print("\n" + "="*60)
print("Populating contraindication_checks table")
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
    
    # Get all prescriptions
    cursor.execute("""
        SELECT id, user_id, medicine_name 
        FROM prescriptions 
        ORDER BY id
    """)
    prescriptions = cursor.fetchall()
    
    if not prescriptions:
        print("✗ No prescriptions found in database")
    else:
        print(f"Found {len(prescriptions)} prescriptions\n")
        
        # Clear existing data
        cursor.execute("DELETE FROM contraindication_checks")
        deleted = cursor.rowcount
        print(f"Cleared {deleted} old records\n")
        
        # Sample contraindication checks
        checks = [
            {
                'check_type': 'drug_interaction',
                'risk_level': 'medium',
                'warning': 'May interact with other medications',
                'recommendation': 'Consult with pharmacist about timing'
            },
            {
                'check_type': 'age_contraindication',
                'risk_level': 'low',
                'warning': 'Requires monitoring in elderly patients',
                'recommendation': 'Regular blood pressure monitoring recommended'
            },
            {
                'check_type': 'allergic_reaction',
                'risk_level': 'high',
                'warning': 'Known allergic reactions reported',
                'recommendation': 'Use alternative medication if available'
            },
            {
                'check_type': 'condition_contraindication',
                'risk_level': 'medium',
                'warning': 'May worsen existing kidney condition',
                'recommendation': 'Monitor kidney function regularly'
            },
            {
                'check_type': 'side_effect_warning',
                'risk_level': 'low',
                'warning': 'May cause dizziness - avoid driving',
                'recommendation': 'Take in evening or before bedtime'
            }
        ]
        
        print("Creating contraindication checks:\n")
        count = 0
        
        for i, (presc_id, user_id, med_name) in enumerate(prescriptions):
            # Randomly assign 0-2 checks per prescription
            num_checks = random.randint(0, 2)
            
            for _ in range(num_checks):
                check = random.choice(checks)
                
                try:
                    cursor.execute("""
                        INSERT INTO contraindication_checks
                        (prescription_id, user_id, medication_name, check_type, 
                         risk_level, warning_message, recommendation, is_acknowledged, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    """, (
                        presc_id, user_id, med_name,
                        check['check_type'],
                        check['risk_level'],
                        check['warning'],
                        check['recommendation'],
                        False
                    ))
                    
                    print(f"  ✓ {med_name} | {check['check_type']} [{check['risk_level']}]")
                    count += 1
                except Exception as e:
                    print(f"  ✗ Error: {str(e)}")
        
        conn.commit()
        print(f"\n✓ Successfully inserted {count} contraindication checks\n")
        
        # Show summary
        cursor.execute("""
            SELECT risk_level, COUNT(*) as count
            FROM contraindication_checks
            GROUP BY risk_level
            ORDER BY CASE 
                WHEN risk_level = 'high' THEN 1
                WHEN risk_level = 'medium' THEN 2
                WHEN risk_level = 'low' THEN 3
            END
        """)
        
        print("Summary by Risk Level:")
        for risk, cnt in cursor.fetchall():
            print(f"  {risk.upper()}: {cnt} checks")
        
        cursor.execute("""
            SELECT check_type, COUNT(*) as count
            FROM contraindication_checks
            GROUP BY check_type
            ORDER BY count DESC
        """)
        
        print("\nSummary by Check Type:")
        for check_type, cnt in cursor.fetchall():
            print(f"  {check_type}: {cnt} checks")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"✗ Error: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60 + "\n")
