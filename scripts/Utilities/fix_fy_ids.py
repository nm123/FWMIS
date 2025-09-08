import sqlite3
import os
import sys

# Add scripts directory to Python path
scripts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(scripts_dir)

try:
    from config import DB_PATH
except ImportError:
    # Fallback if config.py is missing
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data'))
    DB_PATH = os.path.join(BASE_DIR, 'fruitless.db')
    print(f"Warning: config.py not found, using fallback paths")

def analyze_current_fy_ids():
    """Analyze current financial year IDs and their chronological order"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        print("CURRENT FINANCIAL YEAR IDs:")
        print("=" * 50)

        cursor.execute("""
            SELECT id, start_year, end_year, status, active_period
            FROM financial_years
            ORDER BY start_year ASC
        """)

        fys = cursor.fetchall()
        print(f"Found {len(fys)} financial years:")
        print()

        for fy in fys:
            if len(fy) == 5:
                fy_id, start_year, end_year, status, active_period = fy
            else:
                fy_id, start_year, end_year, status = fy
                active_period = None
            print(f"ID {fy_id}: FY {start_year}-{end_year} ({status})")

        print()
        print("PROPOSED NEW IDs (chronological order):")
        print("-" * 40)

        for i, fy in enumerate(fys, 1):
            if len(fy) == 5:
                fy_id, start_year, end_year, status, active_period = fy
            else:
                fy_id, start_year, end_year, status = fy
                active_period = None
            print(f"ID {fy_id} -> ID {i}: FY {start_year}-{end_year}")

        conn.close()

        return fys

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []

def fix_fy_ids():
    """Fix financial year IDs to be chronological"""
    fys = analyze_current_fy_ids()

    if not fys:
        print("No financial years found!")
        return

    print("\n" + "=" * 60)
    print("STARTING FINANCIAL YEAR ID CORRECTION")
    print("=" * 60)

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Create mapping of old_id to new_id
        id_mapping = {}
        for i, fy in enumerate(fys, 1):
            old_id = fy[0]
            id_mapping[old_id] = i

        print("ID MAPPING:")
        for old_id, new_id in id_mapping.items():
            print(f"  {old_id} -> {new_id}")

        # Use a more robust approach: recreate the table with correct IDs
        print("\n1. Creating temporary financial_years table...")

        # Drop temporary table if it exists
        cursor.execute("DROP TABLE IF EXISTS financial_years_temp")

        # Create temporary table
        cursor.execute("""
            CREATE TABLE financial_years_temp (
                id INTEGER PRIMARY KEY,
                start_year INTEGER NOT NULL,
                end_year INTEGER NOT NULL,
                status TEXT NOT NULL,
                active_period INTEGER
            )
        """)

        # Insert data with new IDs
        for i, fy in enumerate(fys, 1):
            old_id, start_year, end_year, status, active_period = fy
            cursor.execute("""
                INSERT INTO financial_years_temp (id, start_year, end_year, status, active_period)
                VALUES (?, ?, ?, ?, ?)
            """, (i, start_year, end_year, status, active_period))

        # Update all foreign key references first
        print("2. Updating foreign key references...")

        # Get list of existing tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in cursor.fetchall()]

        # Update periods table
        if 'periods' in existing_tables:
            print("  - Updating periods table...")
            for old_id, new_id in id_mapping.items():
                cursor.execute("""
                    UPDATE periods SET fy_id = ? WHERE fy_id = ?
                """, (new_id, old_id))

        # Update cases table
        if 'cases' in existing_tables:
            print("  - Updating cases table...")
            for old_id, new_id in id_mapping.items():
                cursor.execute("""
                    UPDATE cases SET fy_id = ? WHERE fy_id = ?
                """, (new_id, old_id))

        # Update fy_case_counters table
        if 'fy_case_counters' in existing_tables:
            print("  - Updating fy_case_counters table...")
            for old_id, new_id in id_mapping.items():
                cursor.execute("""
                    UPDATE fy_case_counters SET fy_id = ? WHERE fy_id = ?
                """, (new_id, old_id))

        # Update shared_documents table
        if 'shared_documents' in existing_tables:
            print("  - Updating shared_documents table...")
            for old_id, new_id in id_mapping.items():
                cursor.execute("""
                    UPDATE shared_documents SET fy_id = ? WHERE fy_id = ?
                """, (new_id, old_id))

        # Update write_off_submissions table
        if 'write_off_submissions' in existing_tables:
            print("  - Updating write_off_submissions table...")
            for old_id, new_id in id_mapping.items():
                cursor.execute("""
                    UPDATE write_off_submissions SET fy_id = ? WHERE fy_id = ?
                """, (new_id, old_id))

        # Drop old table and rename temp table
        print("3. Replacing financial_years table...")
        cursor.execute("DROP TABLE financial_years")
        cursor.execute("ALTER TABLE financial_years_temp RENAME TO financial_years")

        conn.commit()
        conn.close()

        print("\n" + "=" * 60)
        print("FINANCIAL YEAR ID CORRECTION COMPLETED SUCCESSFULLY!")
        print("=" * 60)

        # Verify the changes
        verify_changes()

    except sqlite3.Error as e:
        print(f"Database error during update: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()

def verify_changes():
    """Verify that the ID changes were applied correctly"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        print("\nVERIFICATION - NEW FINANCIAL YEAR IDs:")
        print("=" * 40)

        cursor.execute("""
            SELECT id, start_year, end_year, status
            FROM financial_years
            ORDER BY id ASC
        """)

        fys = cursor.fetchall()
        for fy in fys:
            fy_id, start_year, end_year, status = fy
            print(f"ID {fy_id}: FY {start_year}-{end_year} ({status})")

        # Check that IDs are sequential
        expected_ids = list(range(1, len(fys) + 1))
        actual_ids = [fy[0] for fy in fys]

        if actual_ids == expected_ids:
            print("\n[SUCCESS] IDs are now sequential and chronological!")
        else:
            print(f"\n[ERROR] IDs are not sequential. Expected: {expected_ids}, Got: {actual_ids}")

        # Check foreign key references
        print("\nCHECKING FOREIGN KEY REFERENCES:")

        # Check periods
        cursor.execute("SELECT COUNT(*) FROM periods WHERE fy_id NOT IN (SELECT id FROM financial_years)")
        orphaned_periods = cursor.fetchone()[0]
        print(f"Orphaned periods: {orphaned_periods}")

        # Check cases
        cursor.execute("SELECT COUNT(*) FROM cases WHERE fy_id NOT IN (SELECT id FROM financial_years)")
        orphaned_cases = cursor.fetchone()[0]
        print(f"Orphaned cases: {orphaned_cases}")

        # Check fy_case_counters
        cursor.execute("SELECT COUNT(*) FROM fy_case_counters WHERE fy_id NOT IN (SELECT id FROM financial_years)")
        orphaned_counters = cursor.fetchone()[0]
        print(f"Orphaned fy_case_counters: {orphaned_counters}")

        # Check shared_documents
        cursor.execute("SELECT COUNT(*) FROM shared_documents WHERE fy_id NOT IN (SELECT id FROM financial_years)")
        orphaned_docs = cursor.fetchone()[0]
        print(f"Orphaned shared_documents: {orphaned_docs}")

        # Check write_off_submissions (only if table exists)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='write_off_submissions'")
        if cursor.fetchone():
            cursor.execute("SELECT COUNT(*) FROM write_off_submissions WHERE fy_id NOT IN (SELECT id FROM financial_years)")
            orphaned_submissions = cursor.fetchone()[0]
            print(f"Orphaned write_off_submissions: {orphaned_submissions}")
        else:
            orphaned_submissions = 0
            print("write_off_submissions table does not exist - skipping check")

        if all(count == 0 for count in [orphaned_periods, orphaned_cases, orphaned_counters, orphaned_docs, orphaned_submissions]):
            print("\n[SUCCESS] All foreign key references are valid!")
        else:
            print("\n[ERROR] Some foreign key references are broken!")

        conn.close()

    except sqlite3.Error as e:
        print(f"Database error during verification: {e}")

if __name__ == "__main__":
    print("FINANCIAL YEAR ID CORRECTION TOOL")
    print("=" * 50)

    # First analyze
    fys = analyze_current_fy_ids()

    if fys:
        print("\nProceeding with automatic fix...")
        fix_fy_ids()
    else:
        print("No financial years found to fix.")