import json
from datetime import datetime
from .config import DB_PATH, logging

def save_audit_log(action, details, fy=None):
    from .financial_utils import get_financial_year
    import sqlite3

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