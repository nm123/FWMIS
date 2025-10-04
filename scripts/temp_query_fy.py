import sqlite3

DB_PATH = 'data/fruitless.db'

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

print("Financial Years (id=149 or id=7):")
cur.execute("SELECT * FROM financial_years WHERE id=149 OR id=7")
rows = cur.fetchall()
for row in rows:
    print(row)

print("\nCases in FY 149:")
cur.execute("SELECT COUNT(*) FROM cases WHERE fy_id=149")
count = cur.fetchone()[0]
print(count)

conn.close()