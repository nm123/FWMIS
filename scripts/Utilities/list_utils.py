from .config import DB_PATH, logging

def load_lists():
    import sqlite3
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
                supporting_evidence_path TEXT,
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
                fy_id INTEGER,
                loss_control_recommendation TEXT,
                recovery_evidence_path TEXT
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

        # Alter cases table to add missing columns if not exist
        cursor.execute("PRAGMA table_info(cases)")
        case_columns = [col[1] for col in cursor.fetchall()]
        if 'loss_control_recommendation' not in case_columns:
            cursor.execute("ALTER TABLE cases ADD COLUMN loss_control_recommendation TEXT")
        if 'recovery_evidence_path' not in case_columns:
            cursor.execute("ALTER TABLE cases ADD COLUMN recovery_evidence_path TEXT")
        if 'supporting_evidence_path' not in case_columns:
            cursor.execute("ALTER TABLE cases ADD COLUMN supporting_evidence_path TEXT")

        conn.commit()

        # Auto-create system lists if they don't exist
        system_lists = [
            ("Checklist", True, True),  # name, is_default, is_system
            ("Lead Schedule", False, True),
            ("Deleted Cases", False, True),
            ("Recovered", False, True),
            ("Write-Off Recommended", False, True),
            ("Written Off", False, True)
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
    import sqlite3
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