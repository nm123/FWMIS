import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append('scripts')
sys.path.append('scripts/Utilities')
import sqlite3
from scripts.Utilities.config import DB_PATH

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

columns_to_add = [
    ('bas_journal_no', 'TEXT'),
    ('bas_journal_date', 'DATE'),
    ('assessment_status', 'TEXT'),
    ('lc_status', 'TEXT'),
    ('suffixes', 'TEXT'),
]

added = []
for col_name, col_type in columns_to_add:
    try:
        cur.execute(f"ALTER TABLE cases ADD COLUMN {col_name} {col_type}")
        added.append(col_name)
        print(f"Added column {col_name}")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print(f"Column {col_name} already exists")
        else:
            print(f"Error adding {col_name}: {e}")

conn.commit()
conn.close()

print(f"Successfully added columns: {', '.join(added)}")