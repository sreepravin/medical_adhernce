#!/usr/bin/env python
"""Test the export report endpoint"""

import requests
import json

API_BASE = "http://127.0.0.1:5000/api"

# Test data
report_data = {
    "user_id": 14,
    "username": "sree",
    "email": "sree@example.com"
}

print("="*70)
print("TESTING EXPORT REPORT ENDPOINT")
print("="*70)

try:
    response = requests.post(
        f"{API_BASE}/reports/export",
        json=report_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"\n✓ Response Status: {response.status_code}")
    
    data = response.json()
    print(f"\nResponse:")
    print(json.dumps(data, indent=2))
    
    if data.get('status') == 'success':
        print("\n✓✓ EXPORT ENDPOINT WORKING!")
        print(f"\n✓ Report Data:")
        print(f"  - User: {report_data['username']} (ID: {report_data['user_id']})")
        print(f"  - Email: {report_data['email']}")
        print(f"  - Message: {data['message']}")
    else:
        print("\n✗ Export failed")
        
except Exception as e:
    print(f"\n✗ Error: {e}")
    print("\nMake sure Flask server is running on port 5000")

print("\n" + "="*70)
