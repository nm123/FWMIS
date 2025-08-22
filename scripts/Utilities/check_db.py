import sys
import os
import sqlite3
# Add parent directory (scripts) to Python path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils import BASE_DIR

def check_database():
    db_path = os.path.join(BASE_DIR, "fruitless.db")
    conn = sqlite3.connect(db_path)
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
        cursor.execute("SELECT id, name FROM responsibilities")
        responsibilities = cursor.fetchall()
        print(f"Responsibilities ({len(responsibilities)}): {responsibilities}")
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

    # Check cases
    try:
        cursor.execute("SELECT id, transaction_no, bas_payment_no, category, responsibility_id, amount, status FROM cases")
        cases = cursor.fetchall()
        print(f"Cases ({len(cases)}): {cases}")
    except sqlite3.OperationalError as e:
        print(f"Error checking cases: {e}")

    conn.close()

if __name__ == "__main__":
    check_database()