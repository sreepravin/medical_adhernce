#!/usr/bin/env python
"""Check specific prescription details"""

from db_connection import get_db_connection, execute_query, close_db_connection

conn = get_db_connection()
if conn:
    # Check user 14, prescription 12
    print('Checking user 14, prescription 12:\n')
    
    rx = execute_query(conn, '''
        SELECT id, medicine_name, dosage, frequency, duration, start_date, end_date
        FROM prescriptions
        WHERE id = 12
    ''')
    
    if rx:
        r = rx[0]
        print(f'Prescription ID: {r[0]}')
        print(f'Medicine: {r[1]}')
        print(f'Dosage: {r[2]}')
        print(f'Frequency: {r[3]}')
        print(f'Duration: {r[4]}')
        print(f'Start Date: {r[5]}')
        print(f'End Date: {r[6]}')
    
    print()
    
    # Check adherence plan for this prescription
    plans = execute_query(conn, '''
        SELECT id, daily_schedule, created_at
        FROM adherence_plans
        WHERE prescription_id = 12
    ''')
    
    if plans:
        p = plans[0]
        print(f'Adherence Plan ID: {p[0]}')
        print(f'Daily Schedule: {p[1]}')
        print(f'Created: {p[2]}')
    
    print()
    
    # Check dose tracking for this prescription
    doses = execute_query(conn, '''
        SELECT COUNT(*) as count,
               MIN(scheduled_time) as first_dose,
               MAX(scheduled_time) as last_dose
        FROM dose_tracking
        WHERE prescription_id = 12
    ''')
    
    if doses:
        d = doses[0]
        print(f'Total Dose Entries: {d[0]}')
        print(f'First Dose: {d[1]}')
        print(f'Last Dose: {d[2]}')
    else:
        print('No dose entries found!')
    
    close_db_connection(conn)
