#!/usr/bin/env python3
"""
Test email export functionality
"""
import requests
import json
import time

# Wait for server to start
time.sleep(2)

BASE_URL = "http://localhost:5000"

print("\n" + "="*60)
print("Testing Email Export Functionality")
print("="*60 + "\n")

# Test data
test_data = {
    "user_id": 14,
    "username": "sree",
    "email": "sree@example.com"
}

print(f"Sending export request with:")
print(f"  User ID: {test_data['user_id']}")
print(f"  Username: {test_data['username']}")
print(f"  Email: {test_data['email']}\n")

try:
    response = requests.post(
        f"{BASE_URL}/api/reports/export",
        json=test_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Response Status: {response.status_code}")
    print(f"Response Body:")
    print(json.dumps(response.json(), indent=2))
    
    if response.status_code == 200:
        data = response.json()
        email_sent = data.get('data', {}).get('email_sent', False)
        if email_sent:
            print("\n✓ SUCCESS: Email sent successfully!")
        else:
            print("\n⚠ PARTIAL: Report generated but email not sent.")
            print("  Make sure to configure SMTP settings in .env file:")
            print("  - SMTP_EMAIL: your email address")
            print("  - SMTP_PASSWORD: your app-specific password (for Gmail)")
    else:
        print(f"\n✗ ERROR: {response.status_code}")
        
except Exception as e:
    print(f"✗ Error connecting to server: {str(e)}")
    print("Make sure Flask server is running on port 5000")

print("\n" + "="*60 + "\n")
