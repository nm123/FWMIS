import sqlite3
import json
from datetime import datetime

DB_PATH = '../../data/fruitless.db'

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

log_entry = {
    "timestamp": datetime.now().isoformat(),
    "action": "add_case",
    "details": {"test": "data"},
    "fy": "2025-2026"
}

try:
    cursor.execute(
        "INSERT INTO audit_log (timestamp, action, details, fy) VALUES (?, ?, ?, ?)",
        (log_entry["timestamp"], log_entry["action"], json.dumps(log_entry["details"]), log_entry["fy"])
    )
    print("INSERT succeeded")
    conn.commit()
except Exception as e:
    print(f"INSERT failed: {e}")
    print(f"Error type: {type(e)}")

conn.close()