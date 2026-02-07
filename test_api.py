"""
Test script for Medication Adherence Support System
Run: python test_api.py
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:5000/api"

def print_response(title, response):
    """Pretty print API response"""
    print(f"\n{'='*60}")
    print(f"📋 {title}")
    print(f"{'='*60}")
    print(f"Status Code: {response.status_code}")
    print(f"Response:\n{json.dumps(response.json(), indent=2)}")

def test_health_check():
    """Test API health check"""
    response = requests.get(f"{BASE_URL}/health")
    print_response("Health Check", response)
    return response.status_code == 200

def test_user_registration():
    """Test user registration"""
    user_data = {
        "username": f"testuser_{datetime.now().timestamp()}",
        "email": f"test_{datetime.now().timestamp()}@example.com",
        "full_name": "Test User"
    }
    response = requests.post(f"{BASE_URL}/users/register", json=user_data)
    print_response("User Registration", response)
    
    if response.status_code == 201:
        return response.json()["data"]["id"]
    return None

def test_medical_info(user_id):
    """Test saving medical information"""
    medical_data = {
        "drug_allergies": "Penicillin, Aspirin",
        "food_allergies": "Peanuts",
        "existing_conditions": "Diabetes, High Blood Pressure",
        "current_medications": "Metformin, Lisinopril",
        "is_pregnant": False,
        "is_breastfeeding": False
    }
    response = requests.post(
        f"{BASE_URL}/users/{user_id}/medical-info",
        json=medical_data
    )
    print_response("Save Medical Information", response)
    return response.status_code == 200

def test_get_medical_info(user_id):
    """Test retrieving medical information"""
    response = requests.get(f"{BASE_URL}/users/{user_id}/medical-info")
    print_response("Get Medical Information", response)
    return response.status_code == 200

def test_medication_info():
    """Test getting medication information"""
    response = requests.get(f"{BASE_URL}/medications/metformin")
    print_response("Get Medication Information (Metformin)", response)
    return response.status_code == 200

def test_contraindication_check(user_id):
    """Test contraindication checking"""
    check_data = {
        "user_id": user_id,
        "medicine_name": "Aspirin"
    }
    response = requests.post(f"{BASE_URL}/contraindications", json=check_data)
    print_response("Contraindication Check (Aspirin - User has allergy)", response)
    return response.status_code == 200

def test_manual_prescription_entry(user_id):
    """Test manual prescription entry validation"""
    prescription_data = {
        "user_id": user_id,
        "medicine_name": "Metformin",
        "dosage": "500",
        "dosage_unit": "mg",
        "frequency": "Twice daily",
        "duration": 30,
        "route": "oral",
        "instructions": "Take with meals",
        "prescribed_by": "Dr. Smith"
    }
    response = requests.post(
        f"{BASE_URL}/prescriptions/manual-entry",
        json=prescription_data
    )
    print_response("Manual Prescription Entry", response)
    return response.status_code == 200

def test_save_prescription(user_id):
    """Test saving prescription"""
    prescription_data = {
        "user_id": user_id,
        "medicine_name": "Metformin",
        "dosage": "500",
        "dosage_unit": "mg",
        "frequency": "Twice daily",
        "duration": 30,
        "start_date": datetime.now().date().isoformat(),
        "route": "oral",
        "instructions": "Take with meals",
        "prescribed_by": "Dr. Smith",
        "is_confirmed": True
    }
    response = requests.post(f"{BASE_URL}/prescriptions", json=prescription_data)
    print_response("Save Prescription", response)
    
    if response.status_code == 201:
        return response.json()["data"]["prescription_id"]
    return None

def test_adherence_plan(user_id, prescription_id):
    """Test creating adherence plan"""
    plan_data = {
        "prescription_id": prescription_id,
        "user_id": user_id
    }
    response = requests.post(f"{BASE_URL}/adherence-plans", json=plan_data)
    print_response("Create Adherence Plan", response)
    
    if response.status_code == 201:
        return response.json()["data"]["plan_id"]
    return None

def test_adherence_nudges(prescription_id):
    """Test getting adherence nudges"""
    response = requests.get(f"{BASE_URL}/adherence/nudges/{prescription_id}")
    print_response("Get Adherence Nudges", response)
    return response.status_code == 200

def test_upcoming_reminders(user_id):
    """Test getting upcoming reminders"""
    response = requests.get(f"{BASE_URL}/reminders/upcoming/{user_id}")
    print_response("Get Upcoming Reminders", response)
    return response.status_code == 200

def test_adherence_summary(user_id):
    """Test getting adherence summary"""
    response = requests.get(f"{BASE_URL}/adherence-summary/{user_id}")
    print_response("Get Adherence Summary", response)
    return response.status_code == 200

def test_disclaimer():
    """Test getting safety disclaimer"""
    response = requests.get(f"{BASE_URL}/disclaimer")
    print_response("Safety Disclaimer", response)
    return response.status_code == 200

def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("🧪 MEDICATION ADHERENCE SYSTEM - API TEST SUITE")
    print("="*60)
    
    results = {
        "Health Check": False,
        "User Registration": False,
        "Save Medical Info": False,
        "Get Medical Info": False,
        "Medication Info": False,
        "Contraindication Check": False,
        "Manual Prescription Entry": False,
        "Save Prescription": False,
        "Create Adherence Plan": False,
        "Get Adherence Nudges": False,
        "Upcoming Reminders": False,
        "Adherence Summary": False,
        "Safety Disclaimer": False
    }
    
    # Run tests in sequence
    print("\n🚀 Starting tests...\n")
    
    # Test 1: Health Check
    results["Health Check"] = test_health_check()
    
    # Test 2: User Registration
    user_id = test_user_registration()
    results["User Registration"] = user_id is not None
    
    if user_id:
        # Test 3-13: Other tests
        results["Save Medical Info"] = test_medical_info(user_id)
        results["Get Medical Info"] = test_get_medical_info(user_id)
        results["Medication Info"] = test_medication_info()
        results["Contraindication Check"] = test_contraindication_check(user_id)
        results["Manual Prescription Entry"] = test_manual_prescription_entry(user_id)
        
        prescription_id = test_save_prescription(user_id)
        results["Save Prescription"] = prescription_id is not None
        
        if prescription_id:
            plan_id = test_adherence_plan(user_id, prescription_id)
            results["Create Adherence Plan"] = plan_id is not None
            results["Get Adherence Nudges"] = test_adherence_nudges(prescription_id)
        
        results["Upcoming Reminders"] = test_upcoming_reminders(user_id)
        results["Adherence Summary"] = test_adherence_summary(user_id)
    
    results["Safety Disclaimer"] = test_disclaimer()
    
    # Print summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n{'="*60}")
    print(f"Total: {passed}/{total} tests passed")
    print(f"Success Rate: {passed/total*100:.1f}%")
    print("="*60)
    
    return passed == total

if __name__ == "__main__":
    try:
        success = run_all_tests()
        exit(0 if success else 1)
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to Flask API")
        print("Make sure the server is running: python app.py")
        exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        exit(1)
