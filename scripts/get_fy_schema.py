import sqlite3

DB_PATH = 'data/fruitless.db'

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

print("Schema of financial_years:")
cur.execute("PRAGMA table_info(financial_years)")
rows = cur.fetchall()
for row in rows:
    print(row)

conn.close()