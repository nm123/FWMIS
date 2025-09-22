from .config import DB_PATH, logging


def load_email_templates():
    import sqlite3

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, subject, body FROM email_templates")
        templates = [
            {"id": row[0], "name": row[1], "subject": row[2], "body": row[3]}
            for row in cursor.fetchall()
        ]
        conn.close()
        return templates
    except sqlite3.Error as e:
        logging.error(f"Failed to load email templates: {e}")
        return []


def save_email_templates(templates):
    import sqlite3

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM email_templates")
        for template in templates:
            cursor.execute(
                "INSERT INTO email_templates (id, name, subject, body) VALUES (?, ?, ?, ?)",
                (
                    template["id"],
                    template["name"],
                    template["subject"],
                    template["body"],
                ),
            )
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        logging.error(f"Failed to save email templates: {e}")
