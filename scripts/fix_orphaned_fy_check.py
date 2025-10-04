import sqlite3

DB_PATH = 'data/fruitless.db'

# Connect to the database
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# List all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("All tables in database:")
for table in tables:
    print(f"  - {table[0]}")

# Check if financial_years table exists
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='financial_years'")
schema = cursor.fetchone()
if schema:
    print("\nFinancial Years Schema:")
    print(schema[0])
    
    # Check existing FY records
    cursor.execute("SELECT id, start_year, end_year, status, active_period FROM financial_years ORDER BY id")
    fys = cursor.fetchall()
    print("\nExisting Financial Years:")
    for fy in fys:
        print(f"ID: {fy[0]}, Start: {fy[1]}, End: {fy[2]}, Status: {fy[3]}, Active Period: {fy[4]}")
    
    # Specifically check FY 149
    cursor.execute("SELECT id, start_year, end_year, status, active_period FROM financial_years WHERE id = 149")
    fy149 = cursor.fetchone()
    print(f"\nFY 149: {fy149}")
else:
    print("\nFinancial Years table not found.")

# Check cases table schema for fy_id column
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='cases'")
cases_schema = cursor.fetchone()
if cases_schema:
    print("\nCases Schema:")
    print(cases_schema[0])
    
    # Check cases with fy_id=149
    cursor.execute("SELECT COUNT(*) FROM cases WHERE fy_id = 149 AND list != 'Deleted Cases'")
    try:
        orphaned_count = cursor.fetchone()[0]
        print(f"\nCases with fy_id=149 (non-deleted): {orphaned_count}")
        
        # Sample cases with fy_id=149
        cursor.execute("SELECT id, transaction_no, responsibility_id, category, amount, fy_id, list FROM cases WHERE fy_id = 149 AND list != 'Deleted Cases' LIMIT 3")
        sample_cases = cursor.fetchall()
        print("Sample cases with fy_id=149:")
        for case in sample_cases:
            print(f"  ID: {case[0]}, Trans: {case[1]}, Resp: {case[2]}, Cat: {case[3]}, Amt: {case[4]}, FY: {case[5]}, List: {case[6]}")
    except sqlite3.OperationalError:
        print("\nCases table exists but query failed - possibly no fy_id column.")
else:
    print("\nCases table not found.")

# Check all distinct fy_id in cases
if cases_schema:
    cursor.execute("SELECT DISTINCT fy_id, COUNT(*) FROM cases WHERE list != 'Deleted Cases' GROUP BY fy_id ORDER BY fy_id")
    fy_ids_in_cases = cursor.fetchall()
    print("\nDistinct fy_id values in cases (non-deleted):")
    for fy_id, count in fy_ids_in_cases:
        print(f"  FY ID: {fy_id}, Count: {count}")

conn.close()