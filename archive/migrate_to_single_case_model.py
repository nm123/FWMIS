import json
import os
import sqlite3
import sys
from datetime import datetime

# Add scripts directory to Python path
scripts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(scripts_dir)

try:
    from config import DB_PATH
except ImportError:
    # Fallback if config.py is missing
    BASE_DIR = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "data")
    )
    DB_PATH = os.path.join(BASE_DIR, "fruitless.db")
    print(f"Warning: config.py not found, using fallback paths")


def migrate_to_single_case_model():
    """
    Migrate the database to the new single-case model with suffixes instead of copying.
    This removes the flawed copy-based approach and implements proper workflow tracking.
    """

    if not os.path.exists(DB_PATH):
        print(f"Database not found at: {DB_PATH}")
        return False

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        print("Starting migration to single-case model...")

        # Check if migration already done
        cursor.execute("PRAGMA table_info(cases)")
        columns = [col[1] for col in cursor.fetchall()]

        if "base_transaction_no" in columns:
            print("Migration already completed - base_transaction_no column exists")
            return True

        print("Adding new columns to cases table...")

        # Add new columns
        new_columns = [
            "base_transaction_no TEXT",
            "assessment_status TEXT DEFAULT 'Alleged'",
            "lc_status TEXT",
            "suffixes TEXT DEFAULT ''",
            "write_off_group_id TEXT",
            "evidence_paths TEXT",  # JSON string for file paths
        ]

        for column_def in new_columns:
            try:
                cursor.execute(f"ALTER TABLE cases ADD COLUMN {column_def}")
                print(f"Added column: {column_def}")
            except sqlite3.Error as e:
                print(f"Error adding column {column_def}: {e}")

        print("Migrating existing case data...")

        # Get all existing cases
        cursor.execute(
            """
            SELECT id, transaction_no, status, list, loss_control_recommendation,
                   evidence_path, recovery_evidence_path, minutes, supporting_evidence_path
            FROM cases
        """
        )
        cases = cursor.fetchall()

        for case in cases:
            (
                case_id,
                transaction_no,
                status,
                list_name,
                lc_recommendation,
                evidence_path,
                recovery_path,
                minutes_path,
                supporting_path,
            ) = case

            # Extract base transaction number (remove any existing suffixes)
            base_transaction_no = transaction_no
            suffixes = []

            if "-LS" in transaction_no:
                base_transaction_no = transaction_no.replace("-LS", "")
                suffixes.append("-LS")
            elif "-WOR" in transaction_no:
                base_transaction_no = transaction_no.replace("-WOR", "")
                suffixes.append("-WOR")
            elif "-REC" in transaction_no:
                base_transaction_no = transaction_no.replace("-REC", "")
                suffixes.append("-REC")
            elif "-WO" in transaction_no:
                base_transaction_no = transaction_no.replace("-WO", "")
                suffixes.append("-WO")

            # Determine assessment_status and lc_status based on current status and list
            assessment_status = (
                status
                if status in ["Alleged", "Under Assessment", "Valid", "Confirmed"]
                else "Alleged"
            )
            lc_status = None

            if lc_recommendation:
                if lc_recommendation == "Recovered":
                    lc_status = "Recovered"
                    if "-REC" not in suffixes:
                        suffixes.append("-REC")
                elif lc_recommendation == "Write Off Recommended":
                    lc_status = "Write Off Recommended"
                    if "-WOR" not in suffixes:
                        suffixes.append("-WOR")

            # If status is Written Off, add -WO suffix
            if status == "Written Off":
                lc_status = "Written Off"
                if "-WO" not in suffixes:
                    suffixes.append("-WO")

            # Build evidence paths JSON
            evidence_paths = {}
            if evidence_path:
                evidence_paths["assessment"] = evidence_path
            if recovery_path:
                evidence_paths["recovery"] = recovery_path
            if minutes_path:
                evidence_paths["lc_minutes"] = minutes_path
            if supporting_path:
                evidence_paths["supporting"] = supporting_path

            evidence_paths_json = json.dumps(evidence_paths) if evidence_paths else None

            # Update the case
            cursor.execute(
                """
                UPDATE cases SET
                    base_transaction_no = ?,
                    assessment_status = ?,
                    lc_status = ?,
                    suffixes = ?
                    {evidence_update}
                WHERE id = ?
            """.format(
                    evidence_update=(
                        ", evidence_paths = ?" if evidence_paths_json else ""
                    )
                ),
                (
                    [
                        base_transaction_no,
                        assessment_status,
                        lc_status,
                        ",".join(suffixes),
                    ]
                    + ([evidence_paths_json] if evidence_paths_json else [])
                    + [case_id]
                ),
            )

        # Update is_finalized based on new statuses
        cursor.execute(
            """
            UPDATE cases SET is_finalized = 1
            WHERE assessment_status IN ('Valid') OR lc_status IN ('Recovered', 'Written Off')
        """
        )

        conn.commit()
        print(f"Successfully migrated {len(cases)} cases to single-case model")

        # Create indexes for better performance
        print("Creating indexes for new columns...")
        try:
            cursor.execute(
                "CREATE INDEX idx_cases_base_transaction_no ON cases(base_transaction_no)"
            )
            cursor.execute(
                "CREATE INDEX idx_cases_assessment_status ON cases(assessment_status)"
            )
            cursor.execute("CREATE INDEX idx_cases_lc_status ON cases(lc_status)")
            cursor.execute("CREATE INDEX idx_cases_suffixes ON cases(suffixes)")
            cursor.execute(
                "CREATE INDEX idx_cases_write_off_group_id ON cases(write_off_group_id)"
            )
            print("Indexes created successfully")
        except sqlite3.Error as e:
            print(f"Warning: Could not create indexes: {e}")

        conn.commit()
        print("Migration completed successfully!")
        return True

    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def verify_migration():
    """Verify that the migration was successful"""
    if not os.path.exists(DB_PATH):
        print(f"Database not found at: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Check new columns exist
        cursor.execute("PRAGMA table_info(cases)")
        columns = [col[1] for col in cursor.fetchall()]

        required_columns = [
            "base_transaction_no",
            "assessment_status",
            "lc_status",
            "suffixes",
            "write_off_group_id",
            "evidence_paths",
        ]
        missing_columns = [col for col in required_columns if col not in columns]

        if missing_columns:
            print(f"Migration incomplete - missing columns: {missing_columns}")
            return False

        # Check sample data
        cursor.execute(
            """
            SELECT base_transaction_no, assessment_status, lc_status, suffixes, is_finalized
            FROM cases
            LIMIT 5
        """
        )
        samples = cursor.fetchall()

        print("Sample migrated data:")
        for sample in samples:
            print(
                f"  Base: {sample[0]}, Assessment: {sample[1]}, LC: {sample[2]}, Suffixes: {sample[3]}, Finalized: {sample[4]}"
            )

        # Check counts by status
        cursor.execute(
            "SELECT assessment_status, COUNT(*) FROM cases GROUP BY assessment_status"
        )
        status_counts = cursor.fetchall()
        print("\nCases by assessment status:")
        for status, count in status_counts:
            print(f"  {status}: {count}")

        print("Migration verification completed successfully!")
        return True

    except Exception as e:
        print(f"Verification failed: {e}")
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    print("DATABASE MIGRATION TO SINGLE-CASE MODEL")
    print("=" * 50)

    success = migrate_to_single_case_model()
    if success:
        print("\nVerifying migration...")
        verify_migration()
    else:
        print("Migration failed!")
        sys.exit(1)
