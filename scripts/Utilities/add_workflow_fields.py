import sqlite3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from scripts.Utilities.config import DB_PATH

def add_workflow_fields():
    """Add new fields required for the enhanced case workflow"""

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Check if new fields already exist
        cursor.execute("PRAGMA table_info(cases)")
        columns = [col[1] for col in cursor.fetchall()]

        new_fields = [
            ("determination_amount", "REAL"),
            ("determination_date", "TEXT"),
            ("write_off_submission_id", "TEXT"),
            ("committee_recommendations", "TEXT"),  # JSON field
            ("finalized_date", "TEXT"),
            ("finalization_reason", "TEXT"),
            ("is_finalized", "INTEGER DEFAULT 0")
        ]

        for field_name, field_type in new_fields:
            if field_name not in columns:
                print(f"Adding field: {field_name}")
                cursor.execute(f"ALTER TABLE cases ADD COLUMN {field_name} {field_type}")
            else:
                print(f"Field {field_name} already exists")

        # Create write_off_submissions table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS write_off_submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                submission_id TEXT UNIQUE NOT NULL,
                fy_id INTEGER,
                created_date TEXT NOT NULL,
                submitted_date TEXT,
                approved_date TEXT,
                status TEXT DEFAULT 'Draft',  -- Draft, Submitted, Approved, Rejected
                case_ids TEXT,  -- JSON array of case IDs
                total_amount REAL DEFAULT 0,
                notes TEXT
            )
        """)

        # Create determination_history table for tracking committee determinations
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS determination_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id INTEGER NOT NULL,
                determination_date TEXT NOT NULL,
                determined_amount REAL NOT NULL,
                criminal_charges_recommended INTEGER DEFAULT 0,
                disciplinary_recommended INTEGER DEFAULT 0,
                loss_recovery_recommended INTEGER DEFAULT 0,
                write_off_recommended INTEGER DEFAULT 0,
                committee_members TEXT,  -- JSON array of committee members
                notes TEXT,
                FOREIGN KEY (case_id) REFERENCES cases (id)
            )
        """)

        conn.commit()
        print("Database schema updated successfully!")

        # Show updated schema
        cursor.execute("PRAGMA table_info(cases)")
        updated_columns = cursor.fetchall()
        print(f"\nUpdated cases table has {len(updated_columns)} columns:")
        for col in updated_columns:
            print(f"  {col[1]} ({col[2]})")

    except Exception as e:
        print(f"Error updating database: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    add_workflow_fields()