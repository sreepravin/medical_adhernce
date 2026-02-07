#!/usr/bin/env python3
"""Check users table structure"""

from db_connection import get_db_connection

conn = get_db_connection()
cursor = conn.cursor()

# Check users table structure
cursor.execute('''
    SELECT column_name, data_type, is_nullable 
    FROM information_schema.columns 
    WHERE table_name = 'users' 
    ORDER BY ordinal_position
''')

print('✅ Users table columns:')
print('-' * 70)
columns_list = cursor.fetchall()
for row in columns_list:
    nullable = "Yes" if row[2] == "YES" else "No"
    print(f'  {row[0]:20} | {row[1]:15} | Nullable: {nullable}')

print('\n✅ Checking if date_of_birth and gender exist...')
column_names = [row[0] for row in columns_list]
print(f'   date_of_birth: {"✅ EXISTS" if "date_of_birth" in column_names else "❌ MISSING"}')
print(f'   gender: {"✅ EXISTS" if "gender" in column_names else "❌ MISSING"}')

cursor.close()
conn.close()

