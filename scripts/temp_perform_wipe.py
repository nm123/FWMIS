import sys
import os
import sqlite3
from datetime import datetime

# Add root directory to path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)
sys.path.append('scripts')
sys.path.append('scripts/Utilities')

from scripts.Utilities.config import DB_PATH
from scripts.Utilities.financial_utils import get_all_financial_years, get_current_open_financial_year

print("=== START FULL DATABASE WIPE FOR ALL CASES (NO Qt) ===")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Log to file for debugging
with open("wipe_debug.log", "a") as f:
    f.write(f"\n=== WIPE OPERATION START {datetime.now()} ===\n")
    f.write("Wiping ALL cases (full wipe)\n")

# Clean up any orphaned cases FIRST (cases with invalid fy_id or NULL fy_id)
cursor.execute("""
SELECT COUNT(*) FROM cases
WHERE fy_id NOT IN (SELECT id FROM financial_years) OR fy_id IS NULL
""")
orphaned_count = cursor.fetchone()[0]

if orphaned_count > 0:
    print(f"Found {orphaned_count} orphaned cases - cleaning up")
    cursor.execute("""
    DELETE FROM cases
    WHERE fy_id NOT IN (SELECT id FROM financial_years) OR fy_id IS NULL
    """)
    cleaned_count = cursor.rowcount
    print(f"Cleaned up {cleaned_count} orphaned cases")
else:
    print("No orphaned cases found")
    cleaned_count = 0

# Check installments before deletion - handle if table doesn't exist
installments_exists = False
try:
    cursor.execute("SELECT COUNT(*) FROM installments")
    total_installments_before = cursor.fetchone()[0]
    installments_exists = True
    print(f"Total installments before cleanup: {total_installments_before}")
except sqlite3.OperationalError:
    total_installments_before = 0
    print("Installments table does not exist; skipping count")

with open("wipe_debug.log", "a") as f:
    f.write(f"Total installments before cleanup: {total_installments_before}\n")

# Delete related data that depends on cases BEFORE deleting cases
# Delete installments for all cases (full wipe)
if installments_exists:
    cursor.execute("DELETE FROM installments")
    installments_deleted = cursor.rowcount
    print(f"Deleted {installments_deleted} installments")
else:
    installments_deleted = 0
    print("Installments table does not exist; skipping deletion")

with open("wipe_debug.log", "a") as f:
    f.write(f"Deleted {installments_deleted} installments\n")

# Delete all case attachments/documents
cursor.execute("DELETE FROM shared_documents")
docs_deleted = cursor.rowcount
print(f"Deleted {docs_deleted} shared documents")

# Clean up orphaned periods
cursor.execute("""
SELECT COUNT(*) FROM periods
WHERE fy_id NOT IN (SELECT id FROM financial_years) AND fy_id IS NOT NULL
""")
orphaned_periods_count = cursor.fetchone()[0]

if orphaned_periods_count > 0:
    print(f"Found {orphaned_periods_count} orphaned periods - cleaning up")
    cursor.execute("""
    DELETE FROM periods
    WHERE fy_id NOT IN (SELECT id FROM financial_years) AND fy_id IS NOT NULL
    """)
    cleaned_periods_count = cursor.rowcount
    print(f"Cleaned up {cleaned_periods_count} orphaned periods")
else:
    print("No orphaned periods found")
    cleaned_periods_count = 0

# Delete all cases
cursor.execute("DELETE FROM cases")
cases_deleted = cursor.rowcount
print(f"Deleted {cases_deleted} cases")

# Verify deletion
cursor.execute("SELECT COUNT(*) FROM cases")
after_count = cursor.fetchone()[0]
print(f"Cases remaining: {after_count}")

# Reset all case counters
cursor.execute("UPDATE fy_case_counters SET counter = 0")
counter_updated = cursor.rowcount
print(f"Updated {counter_updated} counter rows")

# Ensure counters exist for all FYs
financial_years = get_all_financial_years()
for fy_id, _, _ in financial_years:
    cursor.execute("""
    INSERT OR IGNORE INTO fy_case_counters (fy_id, counter) VALUES (?, 0)
    """, (fy_id,))
    counter_inserted = cursor.rowcount
    if counter_inserted:
        print(f"Created counter for FY {fy_id}")

# Check all counters
cursor.execute("SELECT fy_id, counter FROM fy_case_counters ORDER BY fy_id")
all_counters = cursor.fetchall()
print(f"All counters: {all_counters}")

conn.commit()
conn.close()

print(f"=== WIPE COMPLETED: Deleted {cases_deleted} cases, {installments_deleted} installments, {docs_deleted} documents ===")

# Final verification
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM cases')
final_cases = cur.fetchone()[0]
print(f'Final case count: {final_cases} (expected 0)')

if installments_exists:
    cur.execute('SELECT COUNT(*) FROM installments')
    final_inst = cur.fetchone()[0]
    print(f'Final installments count: {final_inst} (expected 0)')

conn.close()