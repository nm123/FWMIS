import sqlite3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from scripts.Utilities.config import DB_PATH

def check_active_period():
    """Check the active period for FY 2025-2026"""

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Get FY 2025-2026
        cursor.execute("SELECT id, active_period FROM financial_years WHERE start_year = 2025")
        fy = cursor.fetchone()

        if fy:
            fy_id, active_period = fy
            print(f"FY 2025-2026 ID: {fy_id}, Active Period: {active_period}")

            # Get all periods for this FY
            cursor.execute("SELECT period_number, status FROM periods WHERE fy_id = ? ORDER BY period_number", (fy_id,))
            periods = cursor.fetchall()

            print("Period statuses:")
            for period_num, status in periods:
                print(f"  Period {period_num}: {status}")
        else:
            print("FY 2025-2026 not found")

        conn.close()

    except sqlite3.Error as e:
        print(f"Database error: {e}")

if __name__ == "__main__":
    check_active_period()