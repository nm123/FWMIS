import sqlite3

DB_PATH = 'data/fruitless.db'

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Delete any FY 149 if exists
cur.execute('DELETE FROM financial_years WHERE id=149')

# Update existing FY 7 to 2025-2026
cur.execute('''
    UPDATE financial_years 
    SET start_year=2025, end_year=2026, fy_string='2025-2026' 
    WHERE id=7
''')

# Ensure status is open, active_period NULL (assuming it is, but set if needed)
cur.execute('''
    UPDATE financial_years 
    SET status='open', active_period=NULL 
    WHERE id=7
''')

# Migrate any cases from 149 to 7 (no op if none)
cur.execute('UPDATE cases SET fy_id=7 WHERE fy_id=149')

conn.commit()

# Verify
print("Updated FY 7:")
cur.execute("SELECT * FROM financial_years WHERE id=7")
row = cur.fetchone()
if row:
    print(row)
else:
    print("FY 7 not found after update")

print("\nCases in FY 7:")
cur.execute("SELECT COUNT(*) FROM cases WHERE fy_id=7")
count = cur.fetchone()[0]
print(count)

print("\nCases in FY 149:")
cur.execute("SELECT COUNT(*) FROM cases WHERE fy_id=149")
count149 = cur.fetchone()[0]
print(count149)

conn.close()