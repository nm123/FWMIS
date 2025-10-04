import sys
import os
sys.path.append('scripts')
sys.path.append('scripts/Utilities')
import sqlite3
from scripts.Utilities.config import DB_PATH

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

print("=== CASES TABLE SCHEMA ===")
cur.execute('PRAGMA table_info(cases)')
columns = cur.fetchall()
for col in columns:
    print(f"Column: {col[1]}, Type: {col[2]}, Not Null: {col[3]}, Default: {col[4]}, PK: {col[5]}")

print("\n=== TABLES IN DATABASE ===")
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cur.fetchall()
for t in tables:
    print(f"Table: {t[0]}")

conn.close()