import os
import logging
import sqlite3
import json
from datetime import datetime

# Set BASE_DIR to the project root
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DATA_DIR = os.path.join(BASE_DIR, 'data')
DB_PATH = os.path.join(DATA_DIR, 'fruitless.db')
os.makedirs(DATA_DIR, exist_ok=True)

# Configure logging
logging.basicConfig(
    filename=os.path.join(DATA_DIR, 'app.log'),
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_financial_year():
    today = datetime.now()
    year = today.year
    if today.month >= 4:
        return f"{year}-{year + 1}"
    return f"{year - 1}-{year}"

def generate_transaction_no(fy):
    """
    Generate transaction number in format YYYY00001 based on financial year
    Example: 202600001, 202600002, etc. for FY 2025-2026
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Extract the ending year from financial year (e.g., "2025-2026" -> 2026)
        fy_end_year = int(fy.split('-')[1])

        # Get or create case counter for this financial year
        cursor.execute("""
            SELECT counter FROM fy_case_counters WHERE fy_id = (
                SELECT id FROM financial_years WHERE start_year = ?
            )
        """, (fy_end_year - 1,))

        result = cursor.fetchone()

        if result:
            counter = result[0] + 1
            cursor.execute("""
                UPDATE fy_case_counters SET counter = ? WHERE fy_id = (
                    SELECT id FROM financial_years WHERE start_year = ?
                )
            """, (counter, fy_end_year - 1))
        else:
            # Create new counter if it doesn't exist
            cursor.execute("""
                SELECT id FROM financial_years WHERE start_year = ?
            """, (fy_end_year - 1,))
            fy_result = cursor.fetchone()

            if fy_result:
                fy_id = fy_result[0]
                counter = 1
                cursor.execute("""
                    INSERT INTO fy_case_counters (fy_id, counter) VALUES (?, ?)
                """, (fy_id, counter))
            else:
                # Fallback to timestamp format if FY not found
                conn.close()
                return f"TRANS-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        conn.commit()
        conn.close()

        # Format as YYYY00001 (padded to 5 digits)
        return f"{fy_end_year}{counter:05d}"

    except sqlite3.Error as e:
        logging.error(f"Failed to generate transaction number: {e}")
        # Fallback to timestamp format
        return f"TRANS-{datetime.now().strftime('%Y%m%d%H%M%S')}"

def create_year_folder(fy):
    folder = os.path.join(DATA_DIR, fy)
    os.makedirs(folder, exist_ok=True)
    return folder

def save_audit_log(action, details, fy=None):
    if not fy:
        fy = get_financial_year()
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "details": details,
        "fy": fy
    }
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO audit_log (timestamp, action, details, fy) VALUES (?, ?, ?, ?)",
            (log_entry["timestamp"], log_entry["action"], json.dumps(log_entry["details"]), log_entry["fy"])
        )
        conn.commit()
        logging.info(f"Audit log saved successfully: {action}")
    except sqlite3.Error as e:
        logging.error(f"Failed to save audit log: {e}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error saving audit log: {e}")
        raise
    finally:
        if conn:
            conn.close()

def get_effective_contacts(responsibility_id):
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

def is_valid_email(email):
    """
    Validate email address with comprehensive checks
    """
    if not email or not isinstance(email, str):
        return False

    email = email.strip()
    if not email:
        return False

    import re
    # More comprehensive email regex pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    # Basic format check
    if not re.match(pattern, email):
        return False

    # Additional checks
    if email.count('@') != 1:
        return False

    local_part, domain_part = email.split('@')

    # Local part checks
    if not local_part or len(local_part) > 64:
        return False

    # Domain part checks
    if not domain_part or len(domain_part) > 253:
        return False

    # Check for consecutive dots
    if '..' in email:
        return False

    # Check that domain has at least one dot
    if '.' not in domain_part:
        return False

    return True

def get_subtree_resp_ids(resp_id, responsibilities):
    result = [resp_id]
    for resp in responsibilities:
        if resp["parent_id"] == resp_id:
            result.extend(get_subtree_resp_ids(resp["id"], responsibilities))
    return result

def load_categories():
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # Alter table to add compulsory columns if not exist
        cursor.execute("PRAGMA table_info(categories)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'persal_compulsory' not in columns:
            cursor.execute("ALTER TABLE categories ADD COLUMN persal_compulsory INTEGER DEFAULT 0")
        if 'bas_payment_compulsory' not in columns:
            cursor.execute("ALTER TABLE categories ADD COLUMN bas_payment_compulsory INTEGER DEFAULT 0")
        conn.commit()
        cursor.execute("SELECT id, name, parent_id, persal_compulsory, bas_payment_compulsory FROM categories")
        categories = [{"id": row[0], "name": row[1], "parent_id": row[2], "persal_compulsory": bool(row[3]), "bas_payment_compulsory": bool(row[4])} for row in cursor.fetchall()]
        return categories
    except sqlite3.Error as e:
        logging.error(f"Failed to load categories: {e}")
        return []
    except Exception as e:
        logging.error(f"Unexpected error loading categories: {e}")
        return []
    finally:
        if conn:
            conn.close()

def save_categories(categories):
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM categories")
        for category in categories:
            cursor.execute(
                "INSERT INTO categories (id, name, parent_id, persal_compulsory, bas_payment_compulsory) VALUES (?, ?, ?, ?, ?)",
                (category["id"], category["name"], category["parent_id"], 1 if category.get("persal_compulsory", False) else 0, 1 if category.get("bas_payment_compulsory", False) else 0)
            )
        conn.commit()
        logging.info(f"Successfully saved {len(categories)} categories")
    except sqlite3.Error as e:
        logging.error(f"Failed to save categories: {e}")
        if conn:
            conn.rollback()
        raise
    except Exception as e:
        logging.error(f"Unexpected error saving categories: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

def load_email_templates():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, subject, body FROM email_templates")
        templates = [{"id": row[0], "name": row[1], "subject": row[2], "body": row[3]} for row in cursor.fetchall()]
        conn.close()
        return templates
    except sqlite3.Error as e:
        logging.error(f"Failed to load email templates: {e}")
        return []

def save_email_templates(templates):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM email_templates")
        for template in templates:
            cursor.execute(
                "INSERT INTO email_templates (id, name, subject, body) VALUES (?, ?, ?, ?)",
                (template["id"], template["name"], template["subject"], template["body"])
            )
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        logging.error(f"Failed to save email templates: {e}")

def load_responsibilities():
    try:
        print(f"Connecting to database: {DB_PATH}")  # Debug line
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='responsibilities'")
        if not cursor.fetchone():
            print("Table 'responsibilities' not found in database")
        cursor.execute("SELECT id, name, parent_id, is_posting_level FROM responsibilities")
        responsibilities = [{"id": row[0], "name": row[1], "parent_id": row[2], "is_posting_level": row[3]} for row in cursor.fetchall()]
        conn.close()
        return responsibilities
    except sqlite3.Error as e:
        logging.error(f"Failed to load responsibilities: {e}")
        print(f"Database error: {e}")  # Debug line
        return []

def load_posting_responsibilities():
    """Load only posting level responsibilities for case creation"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, parent_id, is_posting_level FROM responsibilities WHERE is_posting_level = 1")
        responsibilities = [{"id": row[0], "name": row[1], "parent_id": row[2], "is_posting_level": row[3]} for row in cursor.fetchall()]
        conn.close()
        return responsibilities
    except sqlite3.Error as e:
        logging.error(f"Failed to load posting responsibilities: {e}")
        return []

def load_lists():
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # Create table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lists (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                parent_id INTEGER,
                is_default INTEGER DEFAULT 0,
                is_system INTEGER DEFAULT 0
            )
        """)

        # Create audit_log table (drop if exists to ensure correct schema)
        cursor.execute("DROP TABLE IF EXISTS audit_log")
        cursor.execute("""
            CREATE TABLE audit_log (
                id INTEGER PRIMARY KEY,
                timestamp TEXT NOT NULL,
                action TEXT NOT NULL,
                details TEXT,
                fy TEXT
            )
        """)

        # Create financial_years table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS financial_years (
                id INTEGER PRIMARY KEY,
                start_year INTEGER NOT NULL,
                end_year INTEGER NOT NULL,
                status TEXT DEFAULT 'open',
                active_period INTEGER
            )
        """)

        # Create periods table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS periods (
                id INTEGER PRIMARY KEY,
                fy_id INTEGER NOT NULL,
                period_number INTEGER NOT NULL,
                status TEXT DEFAULT 'closed',
                start_date TEXT,
                end_date TEXT,
                FOREIGN KEY (fy_id) REFERENCES financial_years (id)
            )
        """)

        # Create fy_case_counters table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fy_case_counters (
                id INTEGER PRIMARY KEY,
                fy_id INTEGER NOT NULL,
                counter INTEGER DEFAULT 0,
                FOREIGN KEY (fy_id) REFERENCES financial_years (id)
            )
        """)

        # Create responsibilities table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS responsibilities (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                parent_id INTEGER,
                is_posting_level INTEGER DEFAULT 0
            )
        """)

        # Create contacts table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY,
                responsibility_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                title TEXT,
                telephone TEXT,
                email TEXT,
                FOREIGN KEY (responsibility_id) REFERENCES responsibilities (id)
            )
        """)

        # Create categories table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                parent_id INTEGER,
                persal_compulsory INTEGER DEFAULT 0,
                bas_payment_compulsory INTEGER DEFAULT 0
            )
        """)

        # Create email_templates table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS email_templates (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                subject TEXT,
                body TEXT
            )
        """)

        # Create cases table with all required fields if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cases (
                id INTEGER PRIMARY KEY,
                transaction_no TEXT UNIQUE NOT NULL,
                date_incurred TEXT,
                date_identified TEXT,
                date_reported TEXT,
                description TEXT,
                bas_payment_no TEXT,
                bas_payment_date TEXT,
                persal_no TEXT,
                category TEXT,
                responsibility_id INTEGER,
                amount REAL,
                source_document TEXT,
                minutes TEXT,
                evidence_path TEXT,
                attachments TEXT,
                status TEXT DEFAULT 'Alleged',
                list TEXT DEFAULT 'Checklist',
                original_list TEXT,
                assessment_assessed_by TEXT,
                assessment_date TEXT,
                assessment_result TEXT,
                criminal_charges TEXT DEFAULT 'N/A',
                disciplinary_process TEXT DEFAULT 'N/A',
                loss_recovery TEXT DEFAULT 'N/A',
                prevention_steps TEXT,
                period_id INTEGER,
                fy_id INTEGER
            )
        """)
        # Alter table to add columns if not exist
        cursor.execute("PRAGMA table_info(lists)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'parent_id' not in columns:
            cursor.execute("ALTER TABLE lists ADD COLUMN parent_id INTEGER")
        if 'is_default' not in columns:
            cursor.execute("ALTER TABLE lists ADD COLUMN is_default INTEGER DEFAULT 0")
        if 'is_system' not in columns:
            cursor.execute("ALTER TABLE lists ADD COLUMN is_system INTEGER DEFAULT 0")
        conn.commit()

        # Auto-create system lists if they don't exist
        system_lists = [
            ("Checklist", True, True),  # name, is_default, is_system
            ("Lead Schedule", False, True),
            ("Deleted Cases", False, True)
        ]
        for list_name, is_def, is_sys in system_lists:
            cursor.execute("SELECT id FROM lists WHERE name = ?", (list_name,))
            if not cursor.fetchone():
                cursor.execute(
                    "INSERT INTO lists (name, is_default, is_system) VALUES (?, ?, ?)",
                    (list_name, 1 if is_def else 0, 1 if is_sys else 0)
                )
        conn.commit()

        cursor.execute("SELECT id, name, parent_id, is_default, is_system FROM lists")
        lists = [{"id": row[0], "name": row[1], "parent_id": row[2], "is_default": bool(row[3]), "is_system": bool(row[4])} for row in cursor.fetchall()]
        return lists
    except sqlite3.Error as e:
        logging.error(f"Failed to load lists: {e}")
        return []
    except Exception as e:
        logging.error(f"Unexpected error loading lists: {e}")
        return []
    finally:
        if conn:
            conn.close()

def save_lists(lists):
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM lists")
        for list_item in lists:
            cursor.execute(
                "INSERT INTO lists (id, name, parent_id, is_default, is_system) VALUES (?, ?, ?, ?, ?)",
                (list_item["id"], list_item["name"], list_item["parent_id"],
                 1 if list_item.get("is_default", False) else 0,
                 1 if list_item.get("is_system", False) else 0)
            )
        conn.commit()
        logging.info(f"Successfully saved {len(lists)} lists")
    except sqlite3.Error as e:
        logging.error(f"Failed to save lists: {e}")
        if conn:
            conn.rollback()
        raise
    except Exception as e:
        logging.error(f"Unexpected error saving lists: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

def load_cases():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, transaction_no, bas_payment_no, persal_no, amount, category, responsibility_id, status FROM cases")
        cases = [
            {
                "id": row[0],
                "transaction_no": row[1],
                "bas_payment_no": row[2],
                "persal_no": row[3],
                "amount": row[4],
                "category": row[5],
                "responsibility_id": row[6],
                "status": row[7]
            }
            for row in cursor.fetchall()
        ]
        conn.close()
        return cases
    except sqlite3.Error as e:
        logging.error(f"Failed to load cases: {e}")
        return []