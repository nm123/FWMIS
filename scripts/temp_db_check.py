import sqlite3

DB_PATH = 'data/fruitless.db'

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Total cases in FY7
cursor.execute("SELECT COUNT(*) FROM cases WHERE fy_id=7")
total_fy7 = cursor.fetchone()[0]
print(f"Total cases in FY7: {total_fy7}")

# Interest - Other cases in FY7 resp5
cursor.execute("SELECT COUNT(*) FROM cases WHERE fy_id=7 AND category='Interest - Other' AND responsibility_id=5")
interest_cases = cursor.fetchone()[0]
print(f"Interest - Other cases in FY7 resp5: {interest_cases}")

# Duplicate Supplier Payments cases in FY7 resp5
cursor.execute("SELECT COUNT(*) FROM cases WHERE fy_id=7 AND category='Duplicate Supplier Payments' AND responsibility_id=5")
dsp_cases = cursor.fetchone()[0]
print(f"Duplicate Supplier Payments cases in FY7 resp5: {dsp_cases}")

# List all Interest - Other cases amounts and lists
cursor.execute("""
    SELECT transaction_no, amount, list 
    FROM cases 
    WHERE fy_id=7 AND category='Interest - Other' AND responsibility_id=5 
    ORDER BY amount
""")
interest_details = cursor.fetchall()
print("Interest - Other cases details:")
for row in interest_details:
    list_val = row[2] if row[2] is not None else 'NULL'
    print(f"  Transaction: {row[0]}, Amount: {row[1]}, List: {list_val}")

# DSP case details
cursor.execute("""
    SELECT transaction_no, amount, list 
    FROM cases 
    WHERE fy_id=7 AND category='Duplicate Supplier Payments' AND responsibility_id=5
""")
dsp_details = cursor.fetchall()
print("Duplicate Supplier Payments case details:")
for row in dsp_details:
    list_val = row[2] if row[2] is not None else 'NULL'
    print(f"  Transaction: {row[0]}, Amount: {row[1]}, List: {list_val}")

conn.close()