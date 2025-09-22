import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from scripts.Utilities.config import DB_PATH


def fix_active_period():
    """Fix the active period to be the highest open period"""

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Get FY 2025-2026
        cursor.execute("SELECT id FROM financial_years WHERE start_year = 2025")
        fy = cursor.fetchone()

        if fy:
            fy_id = fy[0]

            # Find the highest open period
            cursor.execute(
                """
                SELECT MAX(period_number) FROM periods
                WHERE fy_id = ? AND status = 'open'
            """,
                (fy_id,),
            )

            max_open_period = cursor.fetchone()[0]

            if max_open_period:
                # Update active_period to the highest open period
                cursor.execute(
                    "UPDATE financial_years SET active_period = ? WHERE id = ?",
                    (max_open_period, fy_id),
                )
                print(f"Updated active period to {max_open_period}")
            else:
                print("No open periods found")

        conn.commit()
        conn.close()

    except sqlite3.Error as e:
        print(f"Database error: {e}")


if __name__ == "__main__":
    fix_active_period()
