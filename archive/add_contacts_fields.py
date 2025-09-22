import os
import sqlite3
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import DB_PATH


def add_contacts_fields():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check existing columns
        cursor.execute("PRAGMA table_info(contacts)")
        existing_columns = [col[1] for col in cursor.fetchall()]

        # Fields to add
        fields_to_add = [
            ("initials", "TEXT"),
            ("names", "TEXT"),
            ("surname", "TEXT"),
            ("job_title", "TEXT"),
        ]

        for field_name, field_type in fields_to_add:
            if field_name not in existing_columns:
                cursor.execute(
                    f"ALTER TABLE contacts ADD COLUMN {field_name} {field_type}"
                )
                print(f"Added column: {field_name}")
            else:
                print(f"Column {field_name} already exists")

        conn.commit()
        conn.close()
        print("Contacts table updated successfully")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    add_contacts_fields()
