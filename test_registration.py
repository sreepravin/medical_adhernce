#!/usr/bin/env python3
"""Test user registration with DOB and gender"""

import requests
import json
from datetime import datetime

API_BASE = 'http://localhost:5000/api'

# Test data with unique username
unique_id = int(datetime.now().timestamp())
test_user = {
    'full_name': 'John Doe Test',
    'email': f'johndoe{unique_id}@example.com',
    'username': f'johndoe{unique_id}',
    'date_of_birth': '1990-05-15',
    'gender': 'Male',
    'password': 'testpass123'
}

print('Testing user registration with DOB and Gender...')
print('-' * 60)
print(f'📝 Sending registration data:')
for key, value in test_user.items():
    if key != 'password':
        print(f'   {key}: {value}')

try:
    response = requests.post(f'{API_BASE}/users/register', json=test_user)
    data = response.json()
    
    print(f'\n📊 Response Status: {response.status_code}')
    print(f'📊 Response: {json.dumps(data, indent=2)}')
    
    if data.get('status') == 'success':
        user_data = data.get('data', {})
        print('\n✅ Registration successful!')
        print(f'   ID: {user_data.get("id")}')
        print(f'   Username: {user_data.get("username")}')
        print(f'   Email: {user_data.get("email")}')
        print(f'   Full Name: {user_data.get("full_name")}')
        print(f'   DOB: {user_data.get("date_of_birth")} ⭐')
        print(f'   Gender: {user_data.get("gender")} ⭐')
    else:
        print(f'\n❌ Registration failed: {data.get("message")}')
        
except Exception as e:
    print(f'\n❌ Error: {e}')
    print('Is Flask server running on http://localhost:5000?')

