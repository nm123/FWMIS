import sqlite3
import sys
import os
from datetime import datetime

# Add the scripts directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scripts.Utilities.config import DB_PATH

def migrate_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create delegation table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS write_off_delegations (
        id INTEGER PRIMARY KEY,
        cfo_limit REAL NOT NULL DEFAULT 50000,
        effective_date TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Create annexures table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS annexures (
        id INTEGER PRIMARY KEY,
        annexure_no TEXT UNIQUE NOT NULL,
        role TEXT NOT NULL,
        financial_year_id INTEGER NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (financial_year_id) REFERENCES financial_years(id)
    )
    """)
    
    # Create annexure-case relationship table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS annexure_cases (
        annexure_id INTEGER NOT NULL,
        case_id INTEGER NOT NULL,
        PRIMARY KEY (annexure_id, case_id),
        FOREIGN KEY (annexure_id) REFERENCES annexures(id),
        FOREIGN KEY (case_id) REFERENCES cases(id)
    )
    """)
    
    # Add status column to cases
    try:
        cursor.execute("ALTER TABLE cases ADD COLUMN write_off_status TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    # Insert initial CFO delegation if none exists
    cursor.execute("SELECT COUNT(*) FROM write_off_delegations")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO write_off_delegations (cfo_limit, effective_date)
        VALUES (50000, ?)
        """, (datetime.now().strftime("%Y-%m-%d"),))
    
    conn.commit()
    conn.close()
    print("✅ Database migration completed successfully!")

if __name__ == "__main__":
    migrate_database()
