#!/usr/bin/env python
"""Check adherence plans and dose tracking data"""

from db_connection import get_db_connection, execute_query, close_db_connection

conn = get_db_connection()
if conn:
    print("=== ADHERENCE PLANS ===\n")
    plans = execute_query(conn, '''
        SELECT ap.id, ap.prescription_id, ap.user_id, ap.daily_schedule, 
               ap.created_at, pr.medicine_name
        FROM adherence_plans ap
        LEFT JOIN prescriptions pr ON ap.prescription_id = pr.id
        ORDER BY ap.created_at DESC
        LIMIT 10
    ''')
    
    if plans:
        print(f'✓ Found {len(plans)} adherence plans:')
        for plan in plans:
            print(f'  Plan ID: {plan[0]} | Prescription: {plan[1]} | User: {plan[2]} | Medicine: {plan[5]}')
            print(f'    Schedule: {plan[3]} | Created: {plan[4]}')
    else:
        print('✗ No adherence plans found')
    
    print(f"\n=== DOSE TRACKING ENTRIES ===\n")
    doses = execute_query(conn, '''
        SELECT COUNT(*), user_id, prescription_id
        FROM dose_tracking
        GROUP BY user_id, prescription_id
        ORDER BY user_id DESC
    ''')
    
    if doses:
        print(f'✓ Dose tracking summary:')
        total_doses = 0
        for count, user_id, presc_id in doses:
            print(f'  User {user_id}, Prescription {presc_id}: {count} tracking entries')
            total_doses += count
        print(f'\n✓ Total dose entries: {total_doses}')
    else:
        print('✗ No dose tracking entries found')
    
    # Check specific user (14 - sree)
    print(f"\n=== DOSE TRACKING FOR USER 14 (TODAY) ===\n")
    today_doses = execute_query(conn, '''
        SELECT dt.id, dt.scheduled_time, dt.status, pr.medicine_name, pr.dosage
        FROM dose_tracking dt
        JOIN prescriptions pr ON dt.prescription_id = pr.id
        WHERE dt.user_id = 14 AND DATE(dt.scheduled_time) = CURRENT_DATE
        ORDER BY dt.scheduled_time
    ''')
    
    if today_doses:
        print(f'✓ Found {len(today_doses)} doses for today:')
        for dose in today_doses:
            print(f'  {dose[1]} - {dose[3]} {dose[4]} ({dose[2]})')
    else:
        print('⚠ No doses scheduled for today for user 14')
        
        # Check what dates have doses
        dates = execute_query(conn, '''
            SELECT DISTINCT DATE(scheduled_time) as date, COUNT(*) as count
            FROM dose_tracking
            WHERE user_id = 14
            GROUP BY DATE(scheduled_time)
            ORDER BY date DESC
            LIMIT 5
        ''')
        
        if dates:
            print('\n  Dates with doses available:')
            for d in dates:
                print(f'    {d[0]}: {d[1]} doses')
    
    close_db_connection(conn)
