import sqlite3
import os
import sys

# Add scripts directory to Python path
scripts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(scripts_dir)

try:
    from utils import BASE_DIR
except ImportError:
    # Fallback if utils.py is missing
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data'))
    print(f"Warning: utils.py not found, using fallback BASE_DIR: {BASE_DIR}")

db_path = os.path.join(BASE_DIR, "fruitless.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("PRAGMA journal_mode=WAL;")
cursor.execute("DELETE FROM contacts WHERE responsibility_id = 28")
cursor.execute("DELETE FROM responsibilities WHERE id = 28")
conn.commit()
cursor.execute("SELECT id, name, parent_id, is_posting_level FROM responsibilities")
print(f"Responsibilities: {cursor.fetchall()}")
cursor.execute("SELECT name, title, telephone, email FROM contacts WHERE responsibility_id = 28")
print(f"Contacts for ID 28: {cursor.fetchall()}")
conn.close()