import sys
import os
import sqlite3

# Define DB_PATH directly
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DATA_DIR = os.path.join(BASE_DIR, 'data')
DB_PATH = os.path.join(DATA_DIR, 'fruitless.db')

def check_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check categories
    try:
        cursor.execute("SELECT id, name FROM categories")
        categories = cursor.fetchall()
        print(f"Categories ({len(categories)}): {categories}")
    except sqlite3.OperationalError as e:
        print(f"Error checking categories: {e}")

    # Check responsibilities
    try:
        cursor.execute("PRAGMA table_info(responsibilities)")
        resp_columns = cursor.fetchall()
        print(f"Responsibilities table columns: {[col[1] for col in resp_columns]}")

        cursor.execute("SELECT id, name, parent_id, is_posting_level FROM responsibilities")
        responsibilities = cursor.fetchall()
        print(f"Responsibilities ({len(responsibilities)}): {responsibilities}")

        # Check posting level responsibilities
        cursor.execute("SELECT id, name FROM responsibilities WHERE is_posting_level = 1")
        posting_resps = cursor.fetchall()
        print(f"Posting Level Responsibilities ({len(posting_resps)}): {posting_resps}")
    except sqlite3.OperationalError as e:
        print(f"Error checking responsibilities: {e}")

    # Check email templates
    try:
        cursor.execute("PRAGMA table_info(email_templates)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"Email Templates table columns: {columns}")
        if 'id' in columns:
            cursor.execute("SELECT id, name FROM email_templates")
        else:
            cursor.execute("SELECT name FROM email_templates")
        email_templates = cursor.fetchall()
        print(f"Email Templates ({len(email_templates)}): {email_templates}")
    except sqlite3.OperationalError as e:
        print(f"Error checking email templates: {e}")

    # Check cases table schema
    try:
        cursor.execute("PRAGMA table_info(cases)")
        case_columns = cursor.fetchall()
        print(f"Cases table columns: {[col[1] for col in case_columns]}")
        print(f"Cases table full info: {case_columns}")

        cursor.execute("SELECT id, transaction_no, bas_payment_no, category, responsibility_id, amount, status FROM cases")
        cases = cursor.fetchall()
        print(f"Cases ({len(cases)}): {cases}")
    except sqlite3.OperationalError as e:
        print(f"Error checking cases: {e}")

    conn.close()

if __name__ == "__main__":
    check_database()