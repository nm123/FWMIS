import sqlite3

DB_PATH = 'data/fruitless.db'

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Step 1: Confirm current state (but we already did, proceeding)

# Step 2: Delete FY 149 if exists (but it doesn't, but include)
cur.execute('DELETE FROM financial_years WHERE id=149')

# Also delete existing FY 7 to allow insert with id=7
cur.execute('DELETE FROM financial_years WHERE id=7')

# Step 3: Insert FY 7 for 2025-2026
cur.execute('''
    INSERT INTO financial_years (id, start_year, end_year, status, active_period, fy_string)
    VALUES (7, 2025, 2026, "open", NULL, "2025-2026")
''')

# Step 4: Migrate cases (from 149 to 7, but since none in 149, and existing in 7 stay)
cur.execute('UPDATE cases SET fy_id=7 WHERE fy_id=149')

conn.commit()

# Verify after changes
print("Financial Years after changes:")
cur.execute("SELECT * FROM financial_years WHERE id=7")
row = cur.fetchone()
print(row)

print("\nCases in FY 7:")
cur.execute("SELECT COUNT(*) FROM cases WHERE fy_id=7")
count = cur.fetchone()[0]
print(count)

conn.close()