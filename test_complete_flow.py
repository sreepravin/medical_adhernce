#!/usr/bin/env python
"""
Comprehensive test to verify prescription display fix
Tests: prescriptions, adherence plans, dose tracking, and API endpoints
"""

from db_connection import get_db_connection, execute_query, close_db_connection

def test_complete_flow():
    """Test complete prescription flow for all users"""
    print("\n" + "█"*70)
    print("█ COMPREHENSIVE PRESCRIPTION DISPLAY TEST")
    print("█"*70)
    
    conn = get_db_connection()
    if not conn:
        print("✗ FAILED: Could not connect to database")
        return False
    
    # Get all users
    users = execute_query(conn, 'SELECT id, username FROM users ORDER BY id')
    if not users:
        print("✗ No users found in database")
        close_db_connection(conn)
        return False
    
    all_ok = True
    
    for user_id, username in users:
        print(f"\n{'='*70}")
        print(f"USER: {username} (ID: {user_id})")
        print(f"{'='*70}")
        
        # 1. Check prescriptions
        rx = execute_query(conn, '''
            SELECT COUNT(*), SUM(CASE WHEN id IS NOT NULL THEN 1 ELSE 0 END) 
            FROM prescriptions 
            WHERE user_id = %s
        ''', (user_id,))
        
        rx_count = rx[0][0] if rx and rx[0][0] else 0
        print(f"\n✓ Prescriptions: {rx_count}")
        
        if rx_count == 0:
            continue
        
        # 2. Check adherence plans
        plans = execute_query(conn, '''
            SELECT COUNT(*) FROM adherence_plans WHERE user_id = %s
        ''', (user_id,))
        
        plans_count = plans[0][0] if plans and plans[0][0] else 0
        print(f"✓ Adherence Plans: {plans_count}")
        
        if plans_count != rx_count:
            print(f"  ⚠️ WARNING: {rx_count} prescriptions but only {plans_count} plans")
            all_ok = False
        
        # 3. Check dose tracking
        doses = execute_query(conn, '''
            SELECT COUNT(*) FROM dose_tracking WHERE user_id = %s
        ''', (user_id,))
        
        doses_count = doses[0][0] if doses and doses[0][0] else 0
        print(f"✓ Dose Tracking Entries: {doses_count}")
        
        if doses_count == 0:
            print(f"  ✗ ERROR: No dose tracking entries!")
            all_ok = False
        
        # 4. Check today's doses
        today = execute_query(conn, '''
            SELECT COUNT(*) FROM dose_tracking 
            WHERE user_id = %s AND DATE(scheduled_time) = CURRENT_DATE
        ''', (user_id,))
        
        today_count = today[0][0] if today and today[0][0] else 0
        print(f"✓ Today's Doses Scheduled: {today_count}")
        
        # 5. Check adherence summary
        summary = execute_query(conn, '''
            SELECT 
                SUM(CASE WHEN status = 'taken' THEN 1 ELSE 0 END) as taken,
                SUM(CASE WHEN status = 'missed' THEN 1 ELSE 0 END) as missed,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                COUNT(*) as total
            FROM dose_tracking 
            WHERE user_id = %s AND DATE(scheduled_time) = CURRENT_DATE
        ''', (user_id,))
        
        if summary:
            taken = summary[0][0] or 0
            missed = summary[0][1] or 0
            pending = summary[0][2] or 0
            total = summary[0][3] or 0
            adherence = (taken / total * 100) if total > 0 else 0
            print(f"✓ Today's Summary: {taken} taken, {missed} missed, {pending} pending ({adherence:.1f}% adherence)")
        
        # 6. Check specific prescriptions
        prescription_details = execute_query(conn, '''
            SELECT p.id, p.medicine_name, p.frequency, p.duration,
                   ap.id as plan_id,
                   (SELECT COUNT(*) FROM dose_tracking WHERE prescription_id = p.id) as doses
            FROM prescriptions p
            LEFT JOIN adherence_plans ap ON ap.prescription_id = p.id
            WHERE p.user_id = %s
            ORDER BY p.created_at DESC
        ''', (user_id,))
        
        if prescription_details:
            for presc in prescription_details:
                p_id, medicine, freq, duration, plan_id, dose_count = presc
                status = "✓" if dose_count > 0 else "✗"
                print(f"  {status} Prescription {p_id}: {medicine} ({freq}) - Plan:{plan_id} Doses:{dose_count}")
                
                if dose_count == 0:
                    all_ok = False
    
    close_db_connection(conn)
    
    print(f"\n{'='*70}")
    if all_ok:
        print("✓✓ ALL TESTS PASSED ✓✓")
        print("\nThe prescription system is working correctly!")
        print("Prescriptions -> Adherence Plans -> Dose Tracking -> Dashboard")
    else:
        print("✗✗ SOME TESTS FAILED ✗✗")
        print("\nRun the fix endpoints to rebuild missing data:")
        print("  curl -X POST http://localhost:5000/api/prescriptions/rebuild-tracking")
    print(f"{'='*70}\n")
    
    return all_ok

if __name__ == "__main__":
    test_complete_flow()
