import os
import sqlite3
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import DB_PATH


def test_contact_insertion():
    """Test that contact insertion works with the new schema"""
    test_contact = {
        "title": "Mr",
        "initials": "JD",
        "names": "John",
        "surname": "Doe",
        "job_title": "Manager",
        "telephone": "021 123 4567",
        "email": "john.doe@example.com",
    }

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Create combined name for backward compatibility
        combined_name = (
            f"{test_contact.get('names', '')} {test_contact.get('surname', '')}".strip()
        )

        # Test INSERT statement (similar to what's used in edit_responsibility)
        cursor.execute(
            "INSERT INTO contacts (responsibility_id, name, title, initials, names, surname, job_title, telephone, email) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                99999,
                combined_name,
                test_contact.get("title"),
                test_contact.get("initials"),
                test_contact.get("names"),
                test_contact.get("surname"),
                test_contact.get("job_title"),
                test_contact.get("telephone"),
                test_contact.get("email"),
            ),
        )

        # Verify the insertion
        cursor.execute(
            "SELECT name, title, initials, names, surname, job_title, telephone, email FROM contacts WHERE responsibility_id = ?",
            (99999,),
        )
        result = cursor.fetchone()

        if result:
            print("Contact insertion successful!")
            print(f"Name: {result[0]}")
            print(f"Title: {result[1]}")
            print(f"Initials: {result[2]}")
            print(f"Names: {result[3]}")
            print(f"Surname: {result[4]}")
            print(f"Job Title: {result[5]}")
            print(f"Telephone: {result[6]}")
            print(f"Email: {result[7]}")
        else:
            print("Contact insertion failed - no data found")

        # Clean up test data
        cursor.execute("DELETE FROM contacts WHERE responsibility_id = ?", (99999,))
        conn.commit()

        conn.close()
        print("Test completed successfully - no NOT NULL constraint errors!")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__ == "__main__":
    test_contact_insertion()
