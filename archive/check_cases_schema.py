#!/usr/bin/env python3
import sqlite3
from scripts.Utilities.config import DB_PATH

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("cases table columns:")
cursor.execute('PRAGMA table_info(cases)')
for col in cursor.fetchall():
    print(f"  {col[1]} - {col[2]}")

print("\nSample data from cases (first row):")
cursor.execute('SELECT * FROM cases LIMIT 1')
row = cursor.fetchone()
if row:
    columns = [col[1] for col in cursor.execute('PRAGMA table_info(cases)').fetchall()]
    for i, value in enumerate(row):
        print(f"  {columns[i]}: {value}")
else:
    print("  No data in cases table")

conn.close()
