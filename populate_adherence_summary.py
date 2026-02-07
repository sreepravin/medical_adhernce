#!/usr/bin/env python3
"""
Populate adherence_summary table with data from dose_tracking
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
print("Populating adherence_summary table")
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
    
    # First, check what data we have
    cursor.execute("""
        SELECT DATE_TRUNC('day', scheduled_time)::date as date, 
               user_id,
               COUNT(*) as total_doses,
               SUM(CASE WHEN status = 'taken' THEN 1 ELSE 0 END) as taken,
               SUM(CASE WHEN status = 'missed' THEN 1 ELSE 0 END) as missed
        FROM dose_tracking
        GROUP BY DATE_TRUNC('day', scheduled_time)::date, user_id
        ORDER BY date DESC
    """)
    
    daily_data = cursor.fetchall()
    
    if not daily_data:
        print("✗ No dose tracking data found. Cannot populate adherence_summary.")
        print("Please add prescriptions first.")
    else:
        print(f"Found {len(daily_data)} days of dose tracking data\n")
        
        # Clear existing data
        cursor.execute("DELETE FROM adherence_summary")
        deleted = cursor.rowcount
        print(f"Cleared {deleted} old records\n")
        
        # Insert new data
        count = 0
        for date, user_id, total_doses, taken, missed in daily_data:
            taken = taken or 0
            missed = missed or 0
            adherence_pct = (taken / total_doses * 100) if total_doses > 0 else 0
            
            # Calculate week of month (1-4)
            week_of_month = (date.day - 1) // 7 + 1
            
            cursor.execute("""
                INSERT INTO adherence_summary 
                (user_id, date, total_doses, doses_taken, doses_missed, adherence_percentage, week_of_month, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            """, (user_id, date, total_doses, taken, missed, adherence_pct, week_of_month))
            
            count += 1
            print(f"  {date} | User {user_id} | {taken}/{total_doses} doses | {adherence_pct:.1f}%")
        
        conn.commit()
        print(f"\n✓ Successfully inserted {count} adherence records\n")
        
        # Show summary
        cursor.execute("""
            SELECT user_id, COUNT(*) as days, AVG(adherence_percentage) as avg_adherence
            FROM adherence_summary
            GROUP BY user_id
            ORDER BY user_id
        """)
        
        print("Summary by User:")
        for user_id, days, avg_adh in cursor.fetchall():
            print(f"  User {user_id}: {days} days tracked, {avg_adh:.1f}% average adherence")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"✗ Error: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60 + "\n")
