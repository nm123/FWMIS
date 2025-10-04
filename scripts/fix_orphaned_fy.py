import sqlite3

DB_PATH = 'data/fruitless.db'

def fix_orphaned_fy():
    """One-time fix to insert missing FY 149 record (2025-2026, closed, no active period)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if FY 149 exists
    cursor.execute("SELECT id, start_year, end_year, status, active_period FROM financial_years WHERE id = 149")
    fy149 = cursor.fetchone()
    if not fy149:
        cursor.execute("""
            INSERT INTO financial_years (id, start_year, end_year, status, active_period)
            VALUES (149, 2025, 2026, 'closed', NULL)
        """)
        print("Inserted missing FY record for ID 149 (2025-2026, closed).")
    else:
        print(f"FY 149 already exists: {fy149}")
    
    # Verify cases referencing FY 149
    cursor.execute("""
        SELECT COUNT(*) FROM cases WHERE fy_id = 149 AND list != 'Deleted Cases'
    """)
    orphaned_count = cursor.fetchone()[0]
    print(f"Non-deleted cases referencing FY 149: {orphaned_count}")
    
    if orphaned_count > 0:
        cursor.execute("""
            SELECT transaction_no, category, amount FROM cases
            WHERE fy_id = 149 AND list != 'Deleted Cases' LIMIT 3
        """)
        samples = cursor.fetchall()
        print("Sample cases in FY 149:")
        for sample in samples:
            print(f"  - Transaction: {sample[0]}, Category: {sample[1]}, Amount: {sample[2]}")
    else:
        print("No cases found with fy_id=149. The fix ensures future imports can handle this FY.")
    
    conn.commit()
    conn.close()
    print("Fix applied successfully. This addresses the missing FY record causing duplicate detection failures.")
    print("To prevent future issues, consider enhancing find_duplicates to auto-create missing FY records or migrate orphaned cases.")

if __name__ == "__main__":
    fix_orphaned_fy()