import sqlite3

DB_PATH = 'data/fruitless.db'

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

print("All Financial Years:")
cur.execute("SELECT * FROM financial_years ORDER BY id")
rows = cur.fetchall()
for row in rows:
    print(row)

print("\nCases by FY:")
cur.execute("SELECT fy_id, COUNT(*) FROM cases GROUP BY fy_id")
rows = cur.fetchall()
for row in rows:
    print(row)

conn.close()