#!/usr/bin/env python3
"""Check user data in database"""

from db_connection import get_db_connection

conn = get_db_connection()
cursor = conn.cursor()

# Get all users with their DOB and gender
cursor.execute('''
    SELECT id, username, email, full_name, date_of_birth, gender, created_at
    FROM users
    ORDER BY id
''')

print('✅ All users in database:')
print('-' * 100)
print(f'{"ID":3} | {"Username":15} | {"Email":25} | {"Full Name":15} | {"DOB":10} | {"Gender":15}')
print('-' * 100)

users = cursor.fetchall()
for user in users:
    user_id, username, email, full_name, dob, gender, created_at = user
    dob_str = str(dob) if dob else "NULL"
    gender_str = gender if gender else "NULL"
    print(f'{user_id:3} | {username:15} | {email:25} | {(full_name or ""):15} | {dob_str:10} | {gender_str:15}')

print(f'\n✅ Total users: {len(users)}')
print('\n❌ Users with NULL DOB:', sum(1 for u in users if u[4] is None))
print('❌ Users with NULL Gender:', sum(1 for u in users if u[5] is None))

cursor.close()
conn.close()
