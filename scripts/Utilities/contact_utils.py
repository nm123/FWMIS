from .config import DB_PATH, logging

def get_effective_contacts(responsibility_id):
    import sqlite3
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        contacts = []
        current_id = responsibility_id
        while current_id:
            cursor.execute("SELECT name, title, telephone, email FROM contacts WHERE responsibility_id = ?", (current_id,))
            contacts.extend(cursor.fetchall())
            cursor.execute("SELECT parent_id FROM responsibilities WHERE id = ?", (current_id,))
            result = cursor.fetchone()
            current_id = result[0] if result else None
        return [{"name": c[0], "title": c[1], "telephone": c[2], "email": c[3]} for c in contacts]
    except sqlite3.Error as e:
        logging.error(f"Failed to get contacts for responsibility {responsibility_id}: {e}")
        return []
    except Exception as e:
        logging.error(f"Unexpected error getting contacts: {e}")
        return []
    finally:
        if conn:
            conn.close()