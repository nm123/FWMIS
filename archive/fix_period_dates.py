import sqlite3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from scripts.Utilities.config import DB_PATH

def fix_period_dates():
    """Fix period dates for all financial years to use correct financial year dates"""

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Get all financial years
        cursor.execute("SELECT id, start_year, end_year FROM financial_years")
        fys = cursor.fetchall()

        for fy_id, start_year, end_year in fys:
            print(f"Fixing dates for FY {start_year}-{end_year}")

            # Define correct months for financial year
            months = [
                (4, 30), (5, 31), (6, 30), (7, 31), (8, 31), (9, 30),
                (10, 31), (11, 30), (12, 31), (1, 31), (2, 28), (3, 31)
            ]

            for period_num in range(1, 13):
                month_idx = period_num - 1
                month, days = months[month_idx]

                if period_num <= 9:  # April to December of start_year
                    year = start_year
                else:  # January to March of end_year
                    year = end_year

                start_date = f"{year}-{month:02d}-01"
                end_date = f"{year}-{month:02d}-{days:02d}"

                # Update the period dates
                cursor.execute("""
                    UPDATE periods
                    SET start_date = ?, end_date = ?
                    WHERE fy_id = ? AND period_number = ?
                """, (start_date, end_date, fy_id, period_num))

                print(f"  Period {period_num}: {start_date} to {end_date}")

        conn.commit()
        conn.close()

        print("Period dates fixed successfully!")

    except sqlite3.Error as e:
        print(f"Database error: {e}")

if __name__ == "__main__":
    fix_period_dates()