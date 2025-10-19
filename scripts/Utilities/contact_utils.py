from .config import DB_PATH, logging
from .validation_utils import is_valid_email


def get_effective_contacts(responsibility_id):
    import sqlite3

    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        contacts = []
        current_id = responsibility_id
        while current_id:
            cursor.execute(
                (
                    "SELECT title, initials, names, surname, job_title, telephone, "
                    "email FROM contacts WHERE responsibility_id = ?"
                ),
                (current_id,),
            )
            contacts.extend(cursor.fetchall())
            cursor.execute(
                "SELECT parent_id FROM responsibilities WHERE id = ?", (current_id,)
            )
            result = cursor.fetchone()
            current_id = result[0] if result else None
        # Filter out invalid emails and return in specified order
        valid_contacts = []
        for c in contacts:
            email = c[6]  # email is at index 6
            if not email or is_valid_email(email):
                valid_contacts.append(
                    {
                        "title": c[0],
                        "initials": c[1],
                        "names": c[2],
                        "surname": c[3],
                        "job_title": c[4],
                        "telephone": c[5],
                        "email": c[6],
                    }
                )
        return valid_contacts
    except sqlite3.Error as e:
        logging.error(
            f"Failed to get contacts for responsibility {responsibility_id}: {e}"
        )
        return []
    except Exception as e:
        logging.error(f"Unexpected error getting contacts: {e}")
        return []
    finally:
        if conn:
            conn.close()
