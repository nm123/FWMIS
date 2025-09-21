import sqlite3
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import DB_PATH

def reset_contacts():
    # Default contact data
    default_contact = {
        'title': 'Mrs',
        'initials': 'TP',
        'names': 'Thandeka',
        'surname': 'Meyiwa',
        'job_title': 'SFMO',
        'telephone': '033 395 2680',
        'email': 'Thandeka.Mthembu@kznhealth.gov.za'
    }

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Delete all existing contacts
        cursor.execute("DELETE FROM contacts")
        print("Deleted all existing contacts")

        # Get all responsibility IDs
        cursor.execute("SELECT id FROM responsibilities")
        responsibility_ids = [row[0] for row in cursor.fetchall()]
        print(f"Found {len(responsibility_ids)} responsibilities")

        # Insert default contact for each responsibility
        inserted_count = 0
        for resp_id in responsibility_ids:
            # Create a combined name for backward compatibility
            combined_name = f"{default_contact['names']} {default_contact['surname']}"

            cursor.execute("""
                INSERT INTO contacts (responsibility_id, name, title, initials, names, surname, job_title, telephone, email)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                resp_id,
                combined_name,
                default_contact['title'],
                default_contact['initials'],
                default_contact['names'],
                default_contact['surname'],
                default_contact['job_title'],
                default_contact['telephone'],
                default_contact['email']
            ))
            inserted_count += 1

        conn.commit()
        print(f"Inserted default contact for {inserted_count} responsibilities")

        # Verify the changes
        cursor.execute("SELECT COUNT(*) FROM contacts")
        total_contacts = cursor.fetchone()[0]
        print(f"Total contacts in database: {total_contacts}")

        # Show a sample of the inserted contacts
        cursor.execute("""
            SELECT r.name as responsibility_name, c.title, c.initials, c.names, c.surname, c.job_title, c.telephone, c.email
            FROM contacts c
            JOIN responsibilities r ON c.responsibility_id = r.id
            LIMIT 5
        """)
        sample_contacts = cursor.fetchall()

        print("\nSample of inserted contacts:")
        for contact in sample_contacts:
            print(f"Responsibility: {contact[0]}")
            print(f"  Contact: {contact[1]} {contact[2]} {contact[3]} {contact[4]} - {contact[5]}")
            print(f"  Phone: {contact[6]}, Email: {contact[7]}")
            print()

        conn.close()
        print("Contact reset completed successfully!")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    reset_contacts()