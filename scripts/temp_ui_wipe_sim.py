import sys
sys.path.append('scripts')
sys.path.append('scripts/Utilities')
import sqlite3
from scripts.Utilities.config import DB_PATH

print("=== SIMULATION: Testing installments table access in wipe context ===")
print(f"DB_PATH: {DB_PATH}")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Simulate the SELECT COUNT(*) FROM installments at line 540
print("\n1. Testing initial SELECT COUNT(*) FROM installments (line 540 equivalent):")
try:
    cursor.execute("SELECT COUNT(*) FROM installments")
    total_before = cursor.fetchone()[0]
    print(f"Success: Total installments before: {total_before}")
except sqlite3.Error as e:
    print(f"ERROR: {e}")

# Check if table exists (as in the code)
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='installments'")
table_exists = cursor.fetchone() is not None
print(f"\nTable exists check: {table_exists}")

if table_exists:
    # Simulate FY-specific DELETE (would skip if no cases, but test SELECT if needed)
    print("\n2. If table exists, testing FY-specific cleanup (no actual delete):")
    # No delete, just check
    pass
else:
    print("\n2. Table does not exist: Would skip DELETEs, but proceed to next SELECT")

# Simulate the orphaned DELETE check (line 575+)
print("\n3. Testing orphaned cleanup check:")
if table_exists:
    try:
        cursor.execute("DELETE FROM installments WHERE case_id NOT IN (SELECT id FROM cases)")
        orphaned_deleted = cursor.rowcount
        print(f"Would delete {orphaned_deleted} orphaned (simulation only)")
    except sqlite3.Error as e:
        print(f"ERROR in orphaned DELETE: {e}")
else:
    print("Would skip orphaned DELETE")

# Simulate the post-cleanup SELECT COUNT(*) FROM installments at line 596
print("\n4. Testing post-cleanup SELECT COUNT(*) FROM installments (line 596 equivalent):")
try:
    cursor.execute("SELECT COUNT(*) FROM installments")
    total_after = cursor.fetchone()[0]
    print(f"Success: Total installments after: {total_after}")
except sqlite3.Error as e:
    print(f"ERROR: {e}")

conn.close()

print("\n=== SIMULATION COMPLETE ===")
print("Note: No actual deletions performed. This tests the exact SQL statements that may cause errors in perform_wipe.")