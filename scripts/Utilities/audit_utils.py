import json
from datetime import date, datetime

from .config import DB_PATH, logging


def _make_json_serializable(obj):
    """Convert non-JSON serializable objects to strings"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    return str(obj)


def _serialize_details(details):
    """Recursively convert date/datetime objects in details to strings"""
    if isinstance(details, dict):
        return {key: _serialize_details(value) for key, value in details.items()}
    elif isinstance(details, (list, tuple)):
        return [_serialize_details(item) for item in details]
    else:
        return _make_json_serializable(details)


def save_audit_log(action, details, fy=None):
    import sqlite3

    from .financial_utils import get_financial_year

    if not fy:
        fy = get_financial_year()

    # Serialize details to handle date objects
    serializable_details = _serialize_details(details)

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "details": serializable_details,
        "fy": fy,
    }
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO audit_log (timestamp, action, details, fy) VALUES (?, ?, ?, ?)",
            (
                log_entry["timestamp"],
                log_entry["action"],
                json.dumps(log_entry["details"]),
                log_entry["fy"],
            ),
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
