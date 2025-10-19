import os
import sqlite3
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import DB_PATH


def check_contacts_schema():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Get table info
        cursor.execute("PRAGMA table_info(contacts)")
        columns = cursor.fetchall()
        print("Contacts table schema:")
        for col in columns:
            column_desc = (
                "  {}: {} {} {}".format(
                    col[1],
                    col[2],
                    "PRIMARY KEY" if col[5] else "",
                    "NOT NULL" if col[3] else "",
                )
            )
            print(column_desc)

        # Check if table has data
        cursor.execute("SELECT COUNT(*) FROM contacts")
        count = cursor.fetchone()[0]
        print(f"\nTotal contacts: {count}")

        conn.close()
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    check_contacts_schema()
