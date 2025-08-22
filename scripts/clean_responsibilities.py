import sqlite3
import json
import os
from pathlib import Path

BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
db_path = os.path.join(BASE_DIR, "fruitless.db")

def clean_contacts():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, contacts FROM responsibilities")
    rows = cursor.fetchall()
    updated = 0
    for row in rows:
        resp_id, contacts_data = row
        if contacts_data:
            try:
                # Try parsing to validate JSON
                json.loads(contacts_data)
            except json.JSONDecodeError:
                try:
                    # Attempt to fix single quotes
                    fixed_json = contacts_data.replace("'", '"')
                    json.loads(fixed_json)
                    # Update database with fixed JSON
                    cursor.execute("UPDATE responsibilities SET contacts = ? WHERE id = ?", (fixed_json, resp_id))
                    updated += 1
                    print(f"Fixed contacts for responsibility ID {resp_id}")
                except json.JSONDecodeError:
                    # If still invalid, set to empty list
                    cursor.execute("UPDATE responsibilities SET contacts = ? WHERE id = ?", (json.dumps([]), resp_id))
                    updated += 1
                    print(f"Set empty contacts for responsibility ID {resp_id} due to unfixable JSON")
    conn.commit()
    conn.close()
    print(f"Updated {updated} responsibilities")

if __name__ == "__main__":
    clean_contacts()