#!/usr/bin/env python3
import sqlite3
from scripts.Utilities.config import DB_PATH

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute('SELECT COUNT(*) FROM cases')
total_cases = cursor.fetchone()[0]
print(f'Total cases in database: {total_cases}')

cursor.execute('SELECT fy_id, COUNT(*) FROM cases GROUP BY fy_id ORDER BY fy_id')
print('Cases by fy_id:')
for fy_id, count in cursor.fetchall():
    print(f'  fy_id {fy_id}: {count} cases')

cursor.execute('SELECT id, start_year, end_year FROM financial_years ORDER BY id')
print('Financial years:')
for fy_id, start_year, end_year in cursor.fetchall():
    print(f'  {fy_id}: {start_year}-{end_year}')

cursor.execute('SELECT COUNT(*) FROM cases WHERE transaction_no IS NULL')
null_count = cursor.fetchone()[0]
print(f'Cases with NULL transaction_no: {null_count}')

if null_count > 0:
    cursor.execute('SELECT fy_id, COUNT(*) FROM cases WHERE transaction_no IS NULL GROUP BY fy_id')
    print('NULL transaction_no by fy_id:')
    for fy_id, count in cursor.fetchall():
        print(f'  fy_id {fy_id}: {count} cases')

cursor.execute('SELECT COUNT(*) FROM cases WHERE transaction_no IS NOT NULL')
valid_count = cursor.fetchone()[0]
print(f'Cases with valid transaction_no: {valid_count}')

if valid_count > 0:
    cursor.execute('SELECT transaction_no FROM cases WHERE transaction_no IS NOT NULL LIMIT 5')
    print('Sample valid transaction_no:')
    for row in cursor.fetchall():
        print(f'  {row[0]}')

conn.close()
