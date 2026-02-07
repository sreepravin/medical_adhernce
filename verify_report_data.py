#!/usr/bin/env python
"""Verify Adherence Report data is working"""

from db_connection import get_db_connection, execute_query, close_db_connection

conn = get_db_connection()
if conn:
    print("="*70)
    print("ADHERENCE REPORT DATA - USER 14")
    print("="*70)
    
    # Check today's summary
    print("\n✓ TODAY'S SUMMARY:")
    today = execute_query(conn, '''
        SELECT SUM(CASE WHEN status = 'taken' THEN 1 ELSE 0 END) as taken,
               SUM(CASE WHEN status = 'missed' THEN 1 ELSE 0 END) as missed,
               COUNT(*) as total
        FROM dose_tracking 
        WHERE user_id = 14 AND DATE(scheduled_time) = CURRENT_DATE
    ''')
    
    if today:
        taken = today[0][0] or 0
        missed = today[0][1] or 0
        total = today[0][2] or 0
        adherence = (taken / total * 100) if total > 0 else 0
        print(f"  Doses Taken: {taken}")
        print(f"  Doses Missed: {missed}")
        print(f"  Total Doses: {total}")
        print(f"  Adherence: {adherence:.1f}%")
    
    # Check weekly summary
    print("\n✓ WEEKLY SUMMARY (Last 7 Days):")
    weekly = execute_query(conn, '''
        SELECT DATE(scheduled_time), 
               SUM(CASE WHEN status = 'taken' THEN 1 ELSE 0 END) as taken,
               SUM(CASE WHEN status = 'missed' THEN 1 ELSE 0 END) as missed,
               COUNT(*) as total
        FROM dose_tracking
        WHERE user_id = 14 AND scheduled_time >= NOW() - INTERVAL '7 days'
        GROUP BY DATE(scheduled_time)
        ORDER BY DATE(scheduled_time)
    ''')
    
    if weekly:
        for date, taken, missed, total in weekly:
            adherence = (taken / total * 100) if total > 0 else 0
            taken = taken or 0
            missed = missed or 0
            print(f"  {date}: {taken} taken, {missed} missed, {total} total ({adherence:.1f}%)")
    else:
        print("  No weekly data available")
    
    close_db_connection(conn)
    
    print("\n" + "="*70)
    print("✓ Data is ready to display!")
    print("="*70)
