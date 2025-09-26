#!/usr/bin/env python3
import sqlite3
from scripts.Utilities.config import DB_PATH

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute('SELECT COUNT(*) FROM cases')
total_cases = cursor.fetchone()[0]
print(f'Total cases: {total_cases}')

cursor.execute('SELECT transaction_no FROM cases LIMIT 5')
cases = cursor.fetchall()
print('Cases:')
for case in cases:
    print(f'  {case[0]}')

conn.close()
