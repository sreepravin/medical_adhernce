#!/usr/bin/env python
"""
Test and fix prescription display issues
Checks: prescriptions, adherence plans, dose tracking, and summary data
"""

from db_connection import get_db_connection, execute_query, close_db_connection
import json

def test_user_prescriptions(user_id=1):
    """Check all prescription-related data for a user"""
    print("\n" + "="*70)
    print("PRESCRIPTION DATA DIAGNOSTIC FOR USER", user_id)
    print("="*70)
    
    conn = get_db_connection()
    if not conn:
        print("✗ FAILED: Could not connect to database")
        return False
    
    # 1. Check prescriptions
    print("\n--- 1. PRESCRIPTIONS ---")
    prescriptions = execute_query(conn, """
        SELECT id, medicine_name, dosage, dosage_unit, frequency, duration, 
               start_date, end_date, is_confirmed, created_at
        FROM prescriptions 
        WHERE user_id = %s
        ORDER BY created_at DESC
    """, (user_id,))
    
    if prescriptions:
        print(f"✓ Found {len(prescriptions)} prescriptions:")
        for i, rx in enumerate(prescriptions, 1):
            print(f"\n  [{i}] ID: {rx[0]}")
            print(f"      Medicine: {rx[1]}")
            print(f"      Dosage: {rx[2]} {rx[3]}")
            print(f"      Frequency: {rx[4]}")
            print(f"      Duration: {rx[5]} days")
            print(f"      Dates: {rx[6]} to {rx[7]}")
            print(f"      Confirmed: {rx[8]}")
            print(f"      Created: {rx[9]}")
    else:
        print("✗ No prescriptions found for this user")
        close_db_connection(conn)
        return False
    
    # 2. Check adherence plans
    print("\n--- 2. ADHERENCE PLANS ---")
    adherence_plans = execute_query(conn, """
        SELECT ap.id, ap.prescription_id, ap.user_id, ap.daily_schedule, 
               ap.why_important, ap.nudge_reason, ap.created_at
        FROM adherence_plans ap
        WHERE ap.user_id = %s
        ORDER BY ap.created_at DESC
    """, (user_id,))
    
    if adherence_plans:
        print(f"✓ Found {len(adherence_plans)} adherence plans:")
        for i, plan in enumerate(adherence_plans, 1):
            print(f"\n  [{i}] Plan ID: {plan[0]}")
            print(f"      Prescription ID: {plan[1]}")
            print(f"      Daily Schedule: {plan[3]}")
            print(f"      Why Important: {plan[4][:50]}...")
            print(f"      Created: {plan[6]}")
    else:
        print("✗ No adherence plans found for this user")
    
    # 3. Check dose tracking entries
    print("\n--- 3. DOSE TRACKING ---")
    dose_tracking = execute_query(conn, """
        SELECT dt.id, dt.prescription_id, dt.adherence_plan_id,
               dt.scheduled_time, dt.status, pr.medicine_name, pr.dosage, pr.dosage_unit,
               COUNT(*) OVER (PARTITION BY dt.prescription_id) as total_for_rx
        FROM dose_tracking dt
        JOIN prescriptions pr ON dt.prescription_id = pr.id
        WHERE dt.user_id = %s
        ORDER BY dt.scheduled_time DESC
        LIMIT 10
    """, (user_id,))
    
    if dose_tracking:
        print(f"✓ Found {len(dose_tracking)} dose tracking entries (showing last 10):")
        for i, dose in enumerate(dose_tracking, 1):
            print(f"\n  [{i}] Dose ID: {dose[0]}")
            print(f"      Prescription ID: {dose[1]} | Plan ID: {dose[2]}")
            print(f"      Medicine: {dose[5]} {dose[6]} {dose[7]}")
            print(f"      Scheduled: {dose[3]}")
            print(f"      Status: {dose[4]}")
            print(f"      Total doses for this RX: {dose[8]}")
    else:
        print("✗ No dose tracking entries found for this user")
    
    # 4. Check today's doses
    print("\n--- 4. TODAY'S DOSES ---")
    today_doses = execute_query(conn, """
        SELECT dt.id, dt.scheduled_time, dt.status, pr.medicine_name, pr.dosage, pr.dosage_unit
        FROM dose_tracking dt
        JOIN prescriptions pr ON dt.prescription_id = pr.id
        WHERE dt.user_id = %s AND DATE(dt.scheduled_time) = CURRENT_DATE
        ORDER BY dt.scheduled_time
    """, (user_id,))
    
    if today_doses:
        print(f"✓ Found {len(today_doses)} doses scheduled for today:")
        for i, dose in enumerate(today_doses, 1):
            time = dose[1].strftime("%H:%M")
            print(f"  [{i}] {time} - {dose[3]} {dose[4]} {dose[5]} ({dose[2]})")
    else:
        print("⚠ No doses scheduled for today")
    
    # 5. Check adherence summary
    print("\n--- 5. ADHERENCE SUMMARY (Today) ---")
    summary = execute_query(conn, """
        SELECT SUM(CASE WHEN status = 'taken' THEN 1 ELSE 0 END) as taken,
               SUM(CASE WHEN status = 'missed' THEN 1 ELSE 0 END) as missed,
               SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
               COUNT(*) as total
        FROM dose_tracking 
        WHERE user_id = %s AND DATE(scheduled_time) = CURRENT_DATE
    """, (user_id,))
    
    if summary and summary[0]:
        taken, missed, pending, total = summary[0]
        taken = taken or 0
        missed = missed or 0
        pending = pending or 0
        total = total or 0
        adherence = (taken / total * 100) if total > 0 else 0
        print(f"✓ Today's Summary:")
        print(f"  • Taken: {taken}")
        print(f"  • Missed: {missed}")
        print(f"  • Pending: {pending}")
        print(f"  • Total: {total}")
        print(f"  • Adherence: {adherence:.1f}%")
    else:
        print("⚠ No summary data available for today")
    
    close_db_connection(conn)
    
    # Return success if we have prescriptions and adherence plans
    return bool(prescriptions and adherence_plans and dose_tracking)

def test_api_endpoints(user_id=1):
    """Simulate API endpoint calls to check responses"""
    print("\n" + "="*70)
    print("API ENDPOINT TEST SIMULATION")
    print("="*70)
    
    import sys
    sys.path.insert(0, '/root/app')  # Adjust path as needed
    
    conn = get_db_connection()
    if not conn:
        print("✗ FAILED: Could not connect to database")
        return
    
    # Test get_upcoming_reminders
    print("\n--- REMINDERS ENDPOINT TEST ---")
    reminders = execute_query(conn, """
        SELECT dt.id, dt.scheduled_time, dt.status, pr.medicine_name, pr.dosage, pr.dosage_unit
        FROM dose_tracking dt
        JOIN prescriptions pr ON dt.prescription_id = pr.id
        WHERE dt.user_id = %s AND DATE(dt.scheduled_time) = CURRENT_DATE
        ORDER BY dt.scheduled_time
    """, (user_id,))
    
    if reminders:
        print(f"✓ Would return {len(reminders)} reminders:")
        for reminder in reminders[:3]:
            print(f"  • {reminder[3]} {reminder[4]} {reminder[5]} at {reminder[1]} ({reminder[2]})")
    else:
        print("✓ No reminders for today (this is OK)")
    
    # Test get_adherence_summary
    print("\n--- ADHERENCE SUMMARY ENDPOINT TEST ---")
    summary = execute_query(conn, """
        SELECT SUM(CASE WHEN status = 'taken' THEN 1 ELSE 0 END) as doses_taken,
               SUM(CASE WHEN status = 'missed' THEN 1 ELSE 0 END) as doses_missed,
               COUNT(*) as total_doses
        FROM dose_tracking 
        WHERE user_id = %s AND DATE(scheduled_time) = CURRENT_DATE
    """, (user_id,))
    
    if summary:
        taken, missed, total = summary[0]
        taken = taken or 0
        missed = missed or 0
        total = total or 0
        adherence = (taken / total * 100) if total > 0 else 0
        print(f"✓ Would return:")
        print(f"  • Doses taken: {taken}")
        print(f"  • Doses missed: {missed}")
        print(f"  • Total doses: {total}")
        print(f"  • Adherence: {adherence:.1f}%")
    
    close_db_connection(conn)

def main():
    print("\n" + "█"*70)
    print("█ PRESCRIPTION DISPLAY DIAGNOSTIC AND FIX TOOL")
    print("█"*70)
    
    # Test user 1 first (default demo user)
    success = test_user_prescriptions(1)
    test_api_endpoints(1)
    
    if success:
        print("\n" + "="*70)
        print("✓ DATA STRUCTURE IS CORRECT")
        print("="*70)
        print("\nIf prescriptions are not showing in the dashboard:")
        print("1. Refresh the browser (Ctrl+F5)")
        print("2. Check the browser console for JavaScript errors")
        print("3. Verify the API is responding correctly")
    else:
        print("\n" + "="*70)
        print("✗ ISSUES FOUND")
        print("="*70)
        print("\nPossible solutions:")
        print("1. Check that prescriptions are being saved with correct user_id")
        print("2. Verify adherence_plans are being created after prescription save")
        print("3. Ensure dose_tracking entries are being created")
        print("4. Check for database transaction/commit issues")

if __name__ == "__main__":
    main()
