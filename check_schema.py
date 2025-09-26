#!/usr/bin/env python3
import sqlite3
from scripts.Utilities.config import DB_PATH

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("financial_years table columns:")
cursor.execute('PRAGMA table_info(financial_years)')
for col in cursor.fetchall():
    print(f"  {col[1]} - {col[2]}")

print("\nSample data from financial_years:")
cursor.execute('SELECT * FROM financial_years LIMIT 5')
for row in cursor.fetchall():
    print(f"  {row}")

conn.close()
