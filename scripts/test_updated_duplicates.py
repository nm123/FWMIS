import sqlite3

DB_PATH = 'data/fruitless.db'

# Hardcoded values from context: fy_id=7, resp_name='Test' -> id=5, category='Interest - Other'

# First, get the distinct amounts and transaction_no for the test cases
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
    SELECT DISTINCT amount, transaction_no
    FROM cases 
    WHERE fy_id = 7 
      AND category = 'Interest - Other' 
      AND responsibility_id = 5 
      AND (list IS NULL OR list != 'Deleted Cases')
    ORDER BY amount
""")

amount_rows = cursor.fetchall()
test_cases = [(row[0], row[1]) for row in amount_rows]
print(f"Found {len(test_cases)} test cases for Interest - Other in FY 7, resp 5:")
for amt, trans in test_cases:
    print(f"  Amount: {amt}, Transaction: {trans}")

# Now test the duplicate detection query for each
fy_id = 7
resp_id = 5
category = 'Interest - Other'

all_duplicates = 0
excluded_counts = []

for amt, expected_trans in test_cases:
    print(f"\n=== Isolated Test for amount {amt} (expected match: {expected_trans}) ===")
    
    # Potential without list filter
    cursor.execute("""
        SELECT COUNT(*) FROM cases
        WHERE responsibility_id = ?
          AND category = ?
          AND ABS(amount - ?) < 0.01
          AND fy_id = ?
    """, (resp_id, category, amt, fy_id))
    potential_count = cursor.fetchone()[0]
    print(f"Potential duplicates before list filter: {potential_count}")
    
    # Actual with list filter including NULL
    cursor.execute("""
        SELECT id, transaction_no, category, amount, list, fy_id 
        FROM cases
        WHERE responsibility_id = ?
          AND category = ?
          AND ABS(amount - ?) < 0.01
          AND fy_id = ?
          AND (list != 'Deleted Cases' OR list IS NULL)
    """, (resp_id, category, amt, fy_id))
    
    rows = cursor.fetchall()
    num_dups = len(rows)
    all_duplicates += num_dups
    excluded = potential_count - num_dups
    excluded_counts.append(excluded)
    print(f"After list filter (including NULL): {num_dups} matches")
    print(f"Excluded due to list filter: {excluded}")
    
    if rows:
        for row in rows:
            list_val = row[4] if row[4] is not None else 'NULL'
            print(f"  Match: ID={row[0]}, Transaction={row[1]}, Amount={row[3]}, List={list_val}")
    else:
        print("  No matches found - this is unexpected!")

# Summary for multiple tests
print(f"\n=== Summary for Interest - Other tests ===")
print(f"Total duplicates found: {all_duplicates} (expected {len(test_cases)})")
print(f"Excluded counts per test: {excluded_counts} (expected all 0)")
if all(e == 0 for e in excluded_counts):
    print("All tests show 'Excluded 0 cases due to list filter' - NULL handling working!")
else:
    print("Some exclusions still occurring - investigate further")

# Test for the TEST case (list='Checklist', category='Duplicate Supplier Payments', amount=1000.0)
print("\n=== Test for TEST case (should still be detected) ===")
test_category = 'Duplicate Supplier Payments'
test_amt = 1000.0

# Potential without list filter for TEST
cursor.execute("""
    SELECT COUNT(*) FROM cases
    WHERE responsibility_id = ?
      AND category = ?
      AND ABS(amount - ?) < 0.01
      AND fy_id = ?
""", (resp_id, test_category, test_amt, fy_id))
potential_test = cursor.fetchone()[0]
print(f"Potential duplicates before list filter for TEST: {potential_test}")

# Actual with list filter
cursor.execute("""
    SELECT id, transaction_no, category, amount, list 
    FROM cases
    WHERE responsibility_id = ?
      AND category = ?
      AND ABS(amount - ?) < 0.01
      AND fy_id = ?
      AND (list != 'Deleted Cases' OR list IS NULL)
""", (resp_id, test_category, test_amt, fy_id))

test_rows = cursor.fetchall()
test_num = len(test_rows)
excluded_test = potential_test - test_num
print(f"After list filter for TEST: {test_num} matches")
print(f"Excluded due to list filter for TEST: {excluded_test} (expected 0)")

if test_rows:
    for row in test_rows:
        list_val = row[4] if row[4] is not None else 'NULL'
        print(f"  Match: ID={row[0]}, Transaction={row[1]}, Category={row[2]}, Amount={row[3]}, List={list_val}")
else:
    print("  No TEST match found - unexpected!")

# Check for any deleted cases in FY7 to verify exclusion
cursor.execute("""
    SELECT COUNT(*) FROM cases
    WHERE fy_id = ? AND list = 'Deleted Cases'
""", (fy_id,))
deleted_count = cursor.fetchone()[0]
print(f"\n=== Side effect check: Deleted cases in FY {fy_id}: {deleted_count}")

if deleted_count > 0:
    cursor.execute("""
        SELECT id, transaction_no, category, amount, list 
        FROM cases
        WHERE fy_id = ? AND list = 'Deleted Cases'
        LIMIT 3
    """, (fy_id,))
    deleted_samples = cursor.fetchall()
    print("Sample deleted cases:")
    for row in deleted_samples:
        print(f"  ID={row[0]}, Transaction={row[1]}, Category={row[2]}, Amount={row[3]}, List={row[4]}")
    
    # Test if a deleted case would be excluded: pick one if exists
    if deleted_samples:
        del_amt = deleted_samples[0][3]
        del_cat = deleted_samples[0][2]
        cursor.execute("""
            SELECT COUNT(*) FROM cases
            WHERE responsibility_id = ?
              AND category = ?
              AND ABS(amount - ?) < 0.01
              AND fy_id = ?
        """, (resp_id, del_cat, del_amt, fy_id))
        potential_del = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM cases
            WHERE responsibility_id = ?
              AND category = ?
              AND ABS(amount - ?) < 0.01
              AND fy_id = ?
              AND (list != 'Deleted Cases' OR list IS NULL)
        """, (resp_id, del_cat, del_amt, fy_id))
        actual_del = cursor.fetchone()[0]
        
        print(f"Potential matches for deleted case amount {del_amt}: {potential_del}")
        print(f"Actual matches after filter: {actual_del}")
        print(f"Excluded: {potential_del - actual_del} (should include the deleted one in excluded)")
else:
    print("No deleted cases in FY7 - cannot test exclusion directly, but query logic excludes them")

conn.close()

# Note on full user simulation: This script tests the core query logic. For full UI flow with 23-case file, run the application manually: Load data/test_data/test_bas_23_cases.TXT in Import Undisclosed Cases, select FY 2025-2026 (id=7), responsibility 'Test', category 'Interest - Other' for first 6, click Check Duplicates. Expect logs showing 6 duplicates, 0 excluded, first 6 rows marked as duplicates. Then import, expect 17 new cases added (23-6).