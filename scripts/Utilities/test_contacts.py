import sqlite3
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import DB_PATH
from Utilities.contact_utils import get_effective_contacts

def test_contacts():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Get some responsibility ids
        cursor.execute("SELECT id, name FROM responsibilities LIMIT 5")
        responsibilities = cursor.fetchall()
        print("Sample responsibilities:")
        for resp in responsibilities:
            print(f"ID: {resp[0]}, Name: {resp[1]}")

        if responsibilities:
            # Test get_effective_contacts with first responsibility
            resp_id = responsibilities[0][0]
            contacts = get_effective_contacts(resp_id)
            print(f"\nContacts for responsibility {resp_id}:")
            for contact in contacts:
                print(contact)

        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_contacts()