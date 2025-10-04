import sqlite3

DB_PATH = 'data/fruitless.db'

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

print("Cases with fy_id:")
cur.execute("SELECT id, transaction_no, fy_id, category, amount FROM cases ORDER BY id")
rows = cur.fetchall()
for row in rows:
    print(row)

conn.close()