import sqlite3
import os
from pathlib import Path

BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
db_path = os.path.join(BASE_DIR, "fruitless.db")

def fix_cases_schema():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check current schema
    cursor.execute("PRAGMA table_info(cases)")
    columns = [info[1] for info in cursor.fetchall()]
    print("Current cases table columns:", columns)

    # Drop existing cases_new table to avoid conflicts
    cursor.execute("DROP TABLE IF EXISTS cases_new")

    # Create new table with correct schema
    cursor.execute("""
        CREATE TABLE cases_new (
            id INTEGER PRIMARY KEY,
            transaction_no TEXT UNIQUE,
            date_incurred TEXT,
            date_identified TEXT,
            date_reported TEXT,
            description TEXT,
            bas_payment_no TEXT,
            bas_payment_date TEXT,
            persal_no TEXT,
            category TEXT,
            responsibility_id INTEGER,
            amount REAL,
            source_document TEXT,
            minutes TEXT,
            evidence_path TEXT,
            status TEXT,
            list TEXT,
            assessment_assessed_by TEXT,
            assessment_date TEXT,
            assessment_result TEXT
        )
    """)

    # Copy data to new table
    cursor.execute("""
        INSERT INTO cases_new (
            id, transaction_no, date_incurred, date_identified, date_reported, description,
            bas_payment_no, bas_payment_date, persal_no, category, responsibility_id, amount,
            source_document, minutes, evidence_path, status, list, assessment_assessed_by,
            assessment_date, assessment_result
        )
        SELECT
            id, transaction_no, date_incurred, date_identified, date_reported, description,
            bas_payment_no, bas_payment_date, persal_no, category, responsibility_id, amount,
            source_document, minutes, evidence, status, list, assessment_assessed_by,
            assessment_date, assessment_result
        FROM cases
    """)

    # Drop old table and rename new table
    cursor.execute("DROP TABLE IF EXISTS cases")
    cursor.execute("ALTER TABLE cases_new RENAME TO cases")
    conn.commit()
    conn.close()
    print("Cases table schema updated successfully")

if __name__ == "__main__":
    fix_cases_schema()