import sqlite3

conn = sqlite3.connect('data/fruitless.db')
cur = conn.cursor()

print("=== Responsibilities ===")
cur.execute('SELECT id, name FROM responsibilities ORDER BY id')
respons = cur.fetchall()
for r in respons:
    print(f"ID: {r[0]}, Name: '{r[1]}'")

print("\n=== All cases in FY 7 ===")
cur.execute('SELECT id, transaction_no, responsibility_id, category, amount, fy_id, list FROM cases WHERE fy_id=7 ORDER BY id DESC')
all_cases = cur.fetchall()
for row in all_cases:
    print(f"ID: {row[0]}, Trans: {row[1]}, RespID: {row[2]}, Category: '{row[3]}', Amount: {row[4]}, FY: {row[5]}, List: {row[6]}")

print("\n=== Non-deleted cases in FY 7 (list != 'Deleted Cases') ===")
cur.execute('SELECT id, transaction_no, responsibility_id, category, amount, fy_id, list FROM cases WHERE fy_id=7 AND list != "Deleted Cases" ORDER BY id DESC')
non_del_cases = cur.fetchall()
for row in non_del_cases:
    print(f"ID: {row[0]}, Trans: {row[1]}, RespID: {row[2]}, Category: '{row[3]}', Amount: {row[4]}, FY: {row[5]}, List: {row[6]}")

print(f"\nTotal non-deleted cases in FY 7: {len(non_del_cases)}")

conn.close()