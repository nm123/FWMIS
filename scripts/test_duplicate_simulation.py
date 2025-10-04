import sqlite3

DB_PATH = 'data/fruitless.db'

def simulate_find_duplicates(responsibility_name, category_name, amount):
    """Self-contained simulation of find_duplicates logic"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Hardcode current FY as 7 based on DB inspection
        fy_id = 7
        print(f"DEBUG: Using FY ID: {fy_id}")

        # Resolve responsibility ID
        cursor.execute("SELECT id FROM responsibilities WHERE name = ?", (responsibility_name,))
        resp_result = cursor.fetchone()
        resp_id = resp_result[0] if resp_result else None
        print(f"DEBUG: Responsibility '{responsibility_name}' -> ID: {resp_id}")

        if not resp_id:
            print("No responsibility ID found")
            conn.close()
            return []

        transaction_amount = abs(float(amount))

        print(f"DEBUG: Searching for category='{category_name}', amount={transaction_amount}")

        # Check total cases in FY7 non-deleted
        cursor.execute("""
            SELECT COUNT(*) FROM cases 
            WHERE fy_id = ? AND list != 'Deleted Cases'
        """, (fy_id,))
        total_cases = cursor.fetchone()[0]
        print(f"DEBUG: Total non-deleted cases in FY {fy_id}: {total_cases}")

        # Check for this resp in FY7
        cursor.execute("""
            SELECT COUNT(*) FROM cases 
            WHERE responsibility_id = ? AND fy_id = ? AND list != 'Deleted Cases'
        """, (resp_id, fy_id))
        resp_cases = cursor.fetchone()[0]
        print(f"DEBUG: Cases for resp {resp_id} in FY {fy_id}: {resp_cases}")

        # Check exact category match
        cursor.execute("""
            SELECT COUNT(*) FROM cases 
            WHERE responsibility_id = ? AND category = ? AND fy_id = ? AND list != 'Deleted Cases'
        """, (resp_id, category_name, fy_id))
        cat_match = cursor.fetchone()[0]
        print(f"DEBUG: Cases with exact category '{category_name}': {cat_match}")

        # Full duplicate query
        cursor.execute("""
            SELECT id, transaction_no, category, amount, list, fy_id 
            FROM cases
            WHERE responsibility_id = ?
              AND category = ?
              AND ABS(amount - ?) < 0.01
              AND fy_id = ?
              AND list != 'Deleted Cases'
        """, (resp_id, category_name, transaction_amount, fy_id))

        rows = cursor.fetchall()
        print(f"DEBUG: Duplicate query returned {len(rows)} rows")

        duplicates = []
        for row in rows:
            dup = {
                "id": row[0],
                "transaction_no": row[1],
                "category": row[2],
                "amount": row[3],
                "list": row[4],
                "fy_id": row[5]
            }
            duplicates.append(dup)
            print(f"DEBUG: Match found - ID: {row[0]}, Trans: {row[1]}, Cat: '{row[2]}', Amt: {row[3]}, List: {row[4]}")

        # If no matches, check for whitespace issues in category
        if not rows:
            print("No exact matches. Checking for category variations...")
            cursor.execute("""
                SELECT DISTINCT category, COUNT(*) FROM cases 
                WHERE responsibility_id = ? AND fy_id = ? AND list != 'Deleted Cases'
                GROUP BY category
            """, (resp_id, fy_id))
            cat_variations = cursor.fetchall()
            print("DEBUG: Category variations for this resp/FY:")
            for cat, count in cat_variations:
                print(f"  '{cat}' ({count} cases)")

        conn.close()
        return duplicates

    except Exception as e:
        print(f"Error in simulation: {e}")
        return []

# Test matching case from 23-file and DB
print("=== Test 1: Matching Transaction (should find duplicate) ===")
matching_transaction = {
    'responsibility': 'Test',
    'category': 'Duplicate Supplier Payments',
    'amount': 1000.00
}
dups1 = simulate_find_duplicates(matching_transaction['responsibility'], matching_transaction['category'], matching_transaction['amount'])
print(f"\nResult: Found {len(dups1)} duplicates")

# Test non-matching amount
print("\n=== Test 2: Non-Matching Amount ===")
non_matching = {
    'responsibility': 'Test',
    'category': 'Duplicate Supplier Payments',
    'amount': 1500.00
}
dups2 = simulate_find_duplicates(non_matching['responsibility'], non_matching['category'], non_matching['amount'])
print(f"Result: Found {len(dups2)} duplicates")

# Test with Interest category from DB
print("\n=== Test 3: DB Interest Case (should find if category matches) ===")
interest_test = {
    'responsibility': 'Test',
    'category': 'Interest - Other',
    'amount': 168.0  # Matches one DB case
}
dups3 = simulate_find_duplicates(interest_test['responsibility'], interest_test['category'], interest_test['amount'])
print(f"Result: Found {len(dups3)} duplicates")